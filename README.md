# analysis_streamlit

## 概要
本プロジェクトは、**Streamlit** を活用してデータ分析ダッシュボードを作成するものです。主に日報データを可視化し、売上や客数などの指標を分析できるように設計されています。

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
│── src/
│   ├── pages/          # 各ページの処理
│   │   ├── home.py      # アプリのホーム画面
│   │   ├── analytics.py # 分析ページ
│   ├── components/     # 便利なコンポーネント群
│   │   ├── charts.py    # グラフ生成用
│   │   ├── utils.py     # データフレームの作成、よく使うメソッドを保存
│   ├── test/           # テストコード
│   │   ├── test_utils.py
│   ├── app.py          # Streamlit アプリのエントリーポイント
│── data/               # データ保存用のディレクトリ
│   │── config/         # APIキーやトークンを保存
│   │── processed/      # 整形済みデータ
│   │    │── hourly_report/
│   │    │     ├── customer_num # 整形済み時間別データの客数を保存
│   │    │     ├── sales_num    # 整形済み時間別データの売上を保存
│   │── raw/            # 未処理のデータ
│   │    ├── daily_report # 日報を保存
│── README.md           # プロジェクトの説明
│── requirements.txt    # 必要モジュール一覧
```

## 主な機能
### 📊 **データ分析ページ (analytics.py)**
- **日報分析**: 日別の売上・客数・客単価を可視化
- **月別分析**: 月ごとの売上推移・客数推移を可視化
- **曜日別分析**: 曜日ごとの平均売上・平均客数を比較

### 📈 **グラフ作成 (charts.py)**
- 売上や客数のデータを **Matplotlib** を用いて可視化
- スタックバーや棒グラフを使い、直感的にデータを分析

### 🛠 **データ処理 (utils.py)**
- CSVデータの読み込み・加工
- データの集約・フィルタリング

## 使用技術
- **Python 3.10**
- **Streamlit** (データダッシュボード作成)
- **Pandas** (データ処理)
- **Matplotlib** (グラフ作成)
- **jpholiday** (祝日データの処理)
- **gspread** (spreadsheetの操作)
- **oauth2client** (google関連のアクセス用)

## 今後の改善点
- 夜ラーメンの分析
- 昼ラーメンの分析
- アルコールの分析
- 天気の分析
- 日報データをspreadsheetから取得
- plotlyで画像生成


