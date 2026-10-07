# analysis_streamlit

## 概要
「みつか坊主」というラーメン店の売上データを可視化する**Streamlit**ダッシュボードです。日報・時間帯別・月別・曜日別・年間の売上/客数指標に加え、ラーメン/ランチ/アルコールのメニューカテゴリ別分析ができます。データはGoogleスプレッドシートから取得し、グラフ描画は**Plotly**を使用しています。

## 環境構築
本プロジェクトを動作させるには、以下の手順で環境をセットアップしてください。

### 1. 必要なパッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. Streamlit アプリの起動
```bash
streamlit run src/app.py
```

## ファイル構成
```bash
analysis_streamlit/
├── src/
│   ├── app.py                     # エントリーポイント（サイドバーでページ切替）
│   ├── components/
│   │   ├── pages/
│   │   │   ├── home.py            # トップページ＋フィードバック送信フォーム
│   │   │   └── analytics.py       # 各分析ページの本体
│   │   ├── charts/                # グラフ描画専用（Plotly）。詳細はcharts/README.md参照
│   │   │   ├── daily_report/      # 日報/時間別/年間分析ページ用
│   │   │   └── menu_analysis/     # ラーメン/ランチ分析/アルコールページ用
│   │   └── utils/                 # データ取得・整形。詳細はutils/README.md参照
│   │       ├── common/            # 両ドメイン共通（SpreadSheets, Json）
│   │       ├── daily_report/      # 日報/時間別/年間分析ページ用
│   │       └── menu_analysis/     # ラーメン/ランチ分析/アルコールページ用（5段階パイプライン）
│   └── tests/
├── data/
│   ├── config/                    # サービスアカウントキー(.json)（Google認証用、git管理外）
│   └── json/                      # メニュー名→カテゴリのマッピング定義（menu.json 等）
├── docs/                          # 設計メモ
├── README.md
└── requirements.txt
```

日報データ・ラーメン等のメニューカテゴリ別データは、いずれもGoogleスプレッドシートから直接取得しており、ローカルにCSVを置く運用はありません（旧`data/raw/`・`data/processed/`は削除済み）。

`utils/`・`charts/`のより詳しい構成・データの流れは、それぞれの`README.md`を参照してください。

## 画面構成（app.pyのサイドバーメニュー）

| メニュー | 処理関数 | 内容 |
|---|---|---|
| ホーム | `home.show()` | 説明文＋フィードバック投稿フォーム |
| 日報分析 | `daily_report_analysis()` | 月を選び、日別の売上/客数/客単価を表示 |
| 時間別分析 | `hourly_report_analysis()` | 時間帯別売上/客数を曜日集計、2条件の比較機能あり |
| 月別分析 | `monthly_report_analysis()` | 月単位の合計・平均を表示 |
| 曜日別分析 | `weekly_report_analysis()` | 2つの月を比較し、曜日ごとの増減率を表示 |
| ラーメン | `ramen_analysis()` | 昼/夜/深夜のラーメン提供数・売上を円グラフ＋曜日別棒グラフで表示 |
| ランチ分析 | `lunch_ramen_analysis()` | 昼メニューのカテゴリ別・セットメニュー別割合を表示 |
| アルコール | `alchohol_analysis()` | ビール/秋鹿(日本酒)/ワインなどの月別杯数・売上を表示 |
| 年間分析 | `yearly_report_analysis()` | 年単位の合計/平均客数・売上・客単価を表示 |

## データの流れ（概要）

1. `SpreadSheets.py`がGoogle Drive/Sheets APIで認証（`st.secrets`優先、なければ`data/config/*.json`のサービスアカウントキー）
2. 日報系・メニュー分析系それぞれのUtilsが、対応するGoogleスプレッドシートから直接データを取得
3. メニュー分析系（ラーメン/ランチ/アルコール）は、2026-06-01のPOS切り替えをまたいで新旧2つのデータソースを`menu.json`のカテゴリ定義で統一し、1つのグラフに合体させる（詳細は`src/components/utils/menu_analysis/README.md`）
4. `analytics.py`がUtilsからデータを取得し、対応する`*Charts.py`に渡してPlotlyで描画
5. `@st.cache_resource`で各Utils/Chartsクラスをキャッシュし、Googleスプレッドシートへの重複アクセスを防止

## 使用技術
- Python 3.10 / 3.11
- Streamlit（ダッシュボード）
- Pandas / NumPy（データ処理）
- Plotly（グラフ描画）
- jpholiday（祝日判定）
- gspread / oauth2client / google-api-python-client（Googleスプレッドシート・Drive連携）

## 今後の改善予定

現時点で2つの構想があり、どちらも未着手（着手順は未定）。詳細は`docs/2026-09-27_今後の構想_フード統合とAIレポート.md`を参照。

1. **「ラーメン」「ランチ分析」ページの`food_analysis()`への統合**（元の設計は`docs/2026-07-23_フード分析統合_設計方針.md`のフェーズ2、その後の状況を踏まえた最新版は上記構想メモに記載）。商品単位でのランキング機能もここに含む。
2. **AIによる売上要因分析レポートページ**：あらかじめ用意した要因分析の「型」に沿って、プロンプトを起点にLLMがデータを調べ、文章やグラフでレポートを作成するページ。
