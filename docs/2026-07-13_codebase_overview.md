# アプリケーション概要まとめ（2026-07-13）

対象: リポジトリ全体（`streamlit_mitsuka_analysis`）

## 1. 概要

「みつか坊主」というラーメン店の日報データを可視化するStreamlitダッシュボード。
Googleスプレッドシート上の日報・時間別売上・商品別データを取得し、日次/時間別/月次/曜日別/年次/商品カテゴリ別（ラーメン・ランチ・アルコール）の切り口でグラフ表示する。
グラフ描画は元はMatplotlibだったが、`feature/plotly`ブランチでPlotlyへの移行を進めている。

## 2. 現状の注意点

`feature/plotly`ブランチは `origin/main` とのマージが未完了で、以下4ファイルにコンフリクトマーカー
（`<<<<<<< HEAD` / `=======` / `>>>>>>> origin/main`）が残っている（詳細・原因・対応方針は別途整理）。

- `src/components/charts/LunchAnalysisCharts.py`
- `src/components/charts/RamenAnalysisCharts.py`
- `src/components/pages/analytics.py`
- `src/components/utils/HourlyReportAnalysisUtils.py`

このままでは `streamlit run src/app.py` は構文エラーで起動しない。

## 3. ファイル構成（実態。README.mdの記載は旧構成のままで乖離あり）

```
src/
├── app.py                          # エントリーポイント。サイドバーでページ切替
├── components/
│   ├── pages/
│   │   ├── home.py                 # トップページ＋フィードバック送信フォーム
│   │   └── analytics.py            # 各分析ページの本体（グラフ選択・表示ロジック）
│   ├── charts/                     # Plotly描画専用（データ取得はしない）
│   │   ├── DailyReportAnalysisCharts.py
│   │   ├── HourlyReportAnalysisCharts.py
│   │   ├── YearlyReportAnalysisCharts.py
│   │   ├── LunchAnalysisCharts.py
│   │   ├── RamenAnalysisCharts.py
│   │   └── AlcoholAnalysisCharts.py
│   └── utils/                      # データ取得・整形（Googleスプレッドシート/JSON連携）
│       ├── SpreadSheets.py          # gspread/Drive APIの共通ラッパー（他Utilsの基盤）
│       ├── DailyReportAnalysisUtils.py
│       ├── HourlyReportAnalysisUtils.py
│       ├── YearlyReportAnalysisUtils.py
│       ├── LunchAnalysisUtils.py / MidnightAnalysisUtils.py / DinerAnalysisUtils.py
│       ├── AlcoholAnalysisUtils.py
│       ├── GetByProductDf.py        # 商品バリエーション別の売上/販売数を取得しJSONでカテゴリ分類
│       └── Json.py                  # JSON読み込みヘルパー
└── tests/test_utils.py             # 簡易スモークテスト（pytest形式ではない）

data/
├── config/            # サービスアカウントキー(.json)・.env（Google認証用）
├── json/              # 商品名→カテゴリのマッピング定義（lunch.json, alcohol.json 等）
└── raw/daily_report/  # 日報CSV（2022年10月〜2025年3月分）
```

## 4. 画面（app.pyのサイドバーメニュー）と対応機能

| メニュー | 処理関数 | 内容 |
|---|---|---|
| ホーム | `home.show()` | 説明文＋フィードバック投稿フォーム（スプレッドシートに保存） |
| 日報分析 | `daily_report_analysis()` | 月を選び、日別の売上/客数/客単価を棒グラフ表示 |
| 時間別分析 | `hourly_report_analysis()` | 11〜23時の時間帯別売上/客数を曜日集計、2条件の比較機能あり |
| 月別分析 | `monthly_report_analysis()` | 月単位の合計・平均を棒グラフ表示 |
| 曜日別分析 | `weekly_report_analysis()` | 2つの月を比較し、曜日ごとの増減率を`st.metric`で表示 |
| ラーメン | `ramen_analysis()` | 昼/夜/深夜のラーメン提供数・売上を円グラフ＋曜日別棒グラフで表示 |
| ランチ分析 | `lunch_ramen_analysis()` | 昼メニューのカテゴリ別・セットメニュー別割合を円グラフ表示 |
| アルコール | `alchohol_analysis()` | ビール/秋鹿(日本酒)/若尾ワインなどの月別杯数・売上を表示 |
| 年間分析 | `yearly_report_analysis()` | 年単位の合計/平均客数・売上・客単価を表示 |

## 5. データの流れ

1. `SpreadSheets.py` がGoogle Drive/Sheets APIで認証（`st.secrets`優先、なければ`data/config/*.json`のサービスアカウントキー）し、日報・時間別・商品バリエーション別のスプレッドシートを取得。
2. 各`*AnalysisUtils.py`が取得したDataFrameを整形（型変換、曜日・祝日フラグ付与、月別辞書化など）。
3. `GetByProductDf.py`が商品バリエーション別データを`data/json/*.json`のカテゴリ定義（例: `lunch.json`が「カリー」「白味噌」等の商品名リストをカテゴリにマッピング）で分類。
4. `analytics.py`がUtilsからデータを取得し、対応する`*Charts.py`に渡してPlotlyで描画。
5. `@st.cache_resource`で各Utils/Chartsクラスをキャッシュし、Googleスプレッドシートへの重複アクセスを防止。

## 6. 使用技術

- Python 3.10 / 3.11
- Streamlit（ダッシュボード）
- Pandas / NumPy（データ処理）
- Plotly（グラフ描画。移行中で一部Matplotlibも残存）
- jpholiday（祝日判定）
- gspread / oauth2client / google-api-python-client 系（Googleスプレッドシート・Drive連携）

## 7. 気になった軽微なバグ・改善余地

- `AlcoholAnalysisUtils.get_alchol_data` の第一引数が `sef`（`self`のtypo）になっている。
- `Json.read_json_file` が `encoding='-utf-8'`（先頭に余分なハイフン）を指定している。
- `LunchAnalysisUtils` / `MidnightAnalysisUtils` / `DinerAnalysisUtils` はほぼ同一コードで、商品リストの中身しか違わない（共通化の余地あり）。
- `src/tests/test_utils.py` はpytest形式のテスト関数・assertを持たない、手動確認用のスクリプトに近い。
- README.mdの「ファイル構成」「今後の改善点」は古い内容のままで、現状（ラーメン/アルコール/年間分析ページ、Plotly移行など）を反映していない。
