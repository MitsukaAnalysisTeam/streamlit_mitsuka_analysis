# charts/ ディレクトリについて

このディレクトリは**グラフを描画するだけ**の層です。データを取ってきたり集計したりする処理は一切ここには置かず、すべて`../utils/`側で用意されたDataFrameを受け取って、Plotlyのグラフに変換し`st.plotly_chart(...)`でStreamlit画面に出すことだけをします。

```
utils/ が データを作る
   │
   ▼
charts/ が そのデータを グラフに変換して表示する
```

## フォルダ一覧

`../utils/`と同じ分け方（日報系／メニュー分析系）になっています。詳しい理由は[`../utils/README.md`](../utils/README.md)を参照してください。

```
charts/
├── daily_report/        # 日報／時間別／年間分析ページ用のグラフ
│   ├── DailyReportAnalysisCharts.py
│   ├── HourlyReportAnalysisCharts.py
│   └── YearlyReportAnalysisCharts.py
│
└── menu_analysis/        # ラーメン／ランチ分析／アルコールページ用のグラフ
    ├── RamenAnalysisCharts.py    ラーメンの円グラフ（昼/夜/深夜割合）・曜日別棒グラフ
    ├── LunchAnalysisCharts.py    昼カテゴリ別円グラフ・セット内訳円グラフ
    ├── AlcoholAnalysisCharts.py  ビール/秋鹿/ワインの月次推移棒グラフ
    └── ColorPalette.py           カテゴリ名から色を自動生成するヘルパー
```

月別分析・曜日別分析ページは、専用のChartsクラスを持たず`daily_report/`内のクラスを共用しています。

## `ColorPalette.py`について

**カテゴリ名の文字列から自動的に色を計算**します

## グラフを1つ追加/修正したいとき

1. まず`../utils/`側で必要なDataFrameが既に用意されているか確認する（無ければ`utils/README.md`を見て、どの段階に処理を足すべきか判断する）
2. このディレクトリの対応するクラスにメソッドを追加する
3. 描画に使うカテゴリ名・色は、できる限りハードコードせず`CategoryUnifyMap`（`../utils/menu_analysis/s2_classification/`）や`ColorPalette.py`から動的に取得する
