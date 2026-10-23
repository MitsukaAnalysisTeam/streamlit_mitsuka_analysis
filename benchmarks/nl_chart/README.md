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
| `OPENAI_API_KEY` | OpenAI Decisions API（1c） |
| `ANTHROPIC_API_KEY` | Claude Haiku 5.5（1d） |

環境変数が既にあればそちらを優先する。

## ファイル

| ファイル | 内容 |
|---|---|
| `dataset.jsonl` | 質問サンプル（dev 32 / eval 68）と正解ラベル |
| `validate_dataset.py` | ラベルがカタログに収まっているかの検査 |
| `common.py` | 質問・ツール定義の生成、応答の正規化、振り分け（API は呼ばない） |
| `test_common.py` | `common.py` の単体テスト |

```sh
python benchmarks/nl_chart/validate_dataset.py
python benchmarks/nl_chart/test_common.py
```
