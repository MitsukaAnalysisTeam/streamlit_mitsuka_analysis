# nl_chart ベンチマーク

「AIに聞く」で使うモデルの比較検証。計画は `docs/nl_chart_assistant/benchmark.md`。

## API キーの置き場所

リポジトリ直下の `.env` に書く（`.gitignore` 済み。コミットされない）。

```sh
cp .env.example .env   # 作成後、各キーを書き込む
```

| 変数 | 使うもの |
|---|---|
| `TYPESAFE_API_KEY` | Jev（1c） |
| `OPENAI_API_KEY` | OpenAI Decisions API（1c）、フォールバック LLM の GPT-6 Luna（1d） |
| `ANTHROPIC_API_KEY` | Claude Haiku 5.5（任意。比較するときだけ） |

環境変数が既にあればそちらを優先する。

## ファイル

| ファイル | 内容 |
|---|---|
| `dataset.jsonl` | 質問サンプル（dev 32 / eval 68）と正解ラベル |
| `validate_dataset.py` | ラベルがカタログに収まっているかの検査 |
| `common.py` | 質問・ツール定義の生成、応答の正規化、振り分け（API は呼ばない） |
| `test_common.py` | `common.py` の単体テスト |
| `adapters/` | `http_judges.py`（Jev・Decisions）、`openai_llm.py`（GPT-6 Luna）、`claude.py`（Haiku 5.5）。API 呼び出しだけを担当 |
| `run.py` | 質問を投げて、生の応答を `results/` に JSONL で保存する |
| `test_run.py` | アダプタと `run.py` の単体テスト（API は呼ばない） |

```sh
python benchmarks/nl_chart/validate_dataset.py
python benchmarks/nl_chart/test_common.py
```

## 実行

```sh
pip install -r benchmarks/nl_chart/requirements.txt

# まず中身と回数の確認（API は呼ばない・キー不要）
python benchmarks/nl_chart/run.py --adapter jev --model jev-latest --split dev --dry-run

# 判断役: 選択肢の順序なし/シャッフル2通り × 「該当なし」あり・なし
python benchmarks/nl_chart/run.py --adapter jev --model jev-latest --split dev --shuffle-seeds none 1 2 --with-none both
python benchmarks/nl_chart/run.py --adapter jev --model jev-preview --split dev --shuffle-seeds none 1 2 --with-none both
python benchmarks/nl_chart/run.py --adapter decisions --model gpt-6-luna --split dev --shuffle-seeds none 1 2 --with-none both

# フォールバック LLM（第一候補）: 同じ質問を3回
python benchmarks/nl_chart/run.py --adapter openai --model gpt-6-luna --split dev --repeat 3

# Claude Haiku 5.5 と比べるとき（Anthropic のキーが必要）
python benchmarks/nl_chart/run.py --adapter claude --model claude-haiku-5-5 --split dev --repeat 3
```

- 結果は `benchmarks/nl_chart/results/`（コミットしない）。1行が1リクエストで、生の応答・使用量・応答時間・エラーを含む
- 1件の失敗では止まらず、`error` に記録して続ける。キーが未設定なら、走らせ始める前に止まる
- まず `--split dev` で全候補を走らせ、良かった方だけ `--split eval` を走らせる（計画は `docs/nl_chart_assistant/benchmark.md`）
- 初回は `--limit 3` で少数だけ走らせて、応答の形（特に Decisions API の URL と `usage`、Responses API の `usage`）を確認する
