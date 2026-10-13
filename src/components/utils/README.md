# utils/ ディレクトリについて

このディレクトリには、Streamlitアプリの各分析ページが使うデータ加工ロジック（グラフを描く「前」の処理）が入っています。UI表示そのものは`../charts/`が担当し、`utils/`はその材料となるDataFrameを作る役割です。

## このアプリのページ構成

`src/components/pages/analytics.py`には8つの分析ページがあり、大きく2つのグループに分かれます。

| グループ | ページ | 使うデータ |
|---|---|---|
| **日報系**（`daily_report/`） | 日報分析／時間別分析／月別分析／曜日別分析／年間分析 |
| **メニュー分析系**（`menu_analysis/`） | ラーメン／ランチ分析／アルコール |

日報系は比較的シンプルな構造なので、対応する3クラス（`DailyReportAnalysisUtils`/`HourlyReportAnalysisUtils`/`YearlyReportAnalysisUtils`）がそのまま`daily_report/`に並んでいるだけです。

メニュー分析系は「途中でPOSシステムが切り替わった」という事情があり、新旧2つのデータソースを1つの分類体系にまとめる処理が必要です。そのため`menu_analysis/`の中だけ、処理の段階ごとに5つのサブフォルダに分かれています。詳しくは[`menu_analysis/README.md`](menu_analysis/README.md)を見てください。

## フォルダ一覧

```
utils/
├── common/            # 日報系・メニュー分析系どちらからも使う共通処理
│   ├── SpreadSheets.py   Google Sheets APIへの低レベルアクセス
│   └── Json.py           ただのJSONファイル読み込みヘルパー
│
├── daily_report/      # 日報／時間別／月別／曜日別／年間分析ページ用
│   ├── DailyReportAnalysisUtils.py
│   ├── HourlyReportAnalysisUtils.py
│   └── YearlyReportAnalysisUtils.py
│
└── menu_analysis/      # ラーメン／ランチ分析／アルコールページ用（詳細は中のREADME参照）
    ├── s1_data_sources/       生データの読み込み
    ├── s2_classification/     商品名→カテゴリ名の分類ルール
    ├── s3_transaction/        新データ（会計別CSV）だけの集計
    ├── s4_facades/            新旧データの合体
    └── s5_formatting/         グラフ用に1つのDataFrameへ整形
```
