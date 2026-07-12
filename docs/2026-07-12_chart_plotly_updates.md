# チャート改修まとめ（2026-07-12）

対象ブランチ: `feature/plotly`
対象ファイル:

- `src/components/charts/AlcoholAnalysisCharts.py`
- `src/components/charts/DailyReportAnalysisCharts.py`
- `src/components/charts/HourlyReportAnalysisCharts.py`
- `src/components/charts/LunchAnalysisCharts.py`
- `src/components/charts/RamenAnalysisCharts.py`
- `src/components/charts/YearlyReportAnalysisCharts.py`

## 1. 概要

チャート描画をmatplotlib中心からPlotly中心へ統一する作業の続き。
今回は主に「アルコール分析グラフのPlotly移行」と「グラフ操作性・表記の細かな修正」を行った。

## 2. 変更内容

### 2.1 AlcoholAnalysisCharts.py（matplotlib → Plotly 移行）

- `wine_graph` / `akishika_graph` / `beer_graph` / `alchol_graph` の4グラフを、
  `matplotlib` + `st.pyplot` から `plotly.graph_objects` + `st.plotly_chart` に置き換え。
- 月次平均の算出処理（日付インデックス化 → resample → 合計/日数で平均化）を
  共通メソッド `_monthly_avg_df` に集約し、4グラフで重複していたロジックを一本化。
- 積み上げ棒グラフの描画処理も共通メソッド `_stacked_monthly_bar` に集約。
  凡例位置・ホバー表示（`hovermode='x unified'`）・グリッド線・軸フォーマットなどを統一。
- 各グラフの系列・配色（ワイン、秋鹿、ビール、酒類合計）は元の指定を踏襲。
- 未使用となった `matplotlib.pyplot` / `matplotlib.ticker.FuncFormatter` / `numpy` の import を削除。

### 2.2 軸のズーム・パン無効化（`fixedrange=True`）

以下のファイルで、x軸・y軸に `fixedrange=True` を追加し、グラフのドラッグズームや
軸操作を無効化した（数値ラベルやホバー確認以外の誤操作を防止する目的）。

- `AlcoholAnalysisCharts.py`（新規Plotly化グラフ）
- `DailyReportAnalysisCharts.py`（複数グラフのx軸・y軸）
- `HourlyReportAnalysisCharts.py`（x軸・y軸）
- `RamenAnalysisCharts.py`（曜日別グラフのx軸・y軸）
- `YearlyReportAnalysisCharts.py`（`update_xaxes` / `update_yaxes`）

### 2.3 軽微な表記・フォーマット修正

- `LunchAnalysisCharts.py`: `legend` 定義末尾のカンマ抜けなど、`update_layout` 引数の
  末尾カンマを補い、行末の余分な空白を除去（動作への影響なし）。
- `RamenAnalysisCharts.py`: `legend` 定義・`yaxis` の `tickformat` 指定末尾にカンマを追加
  （動作への影響なし、可読性・保守性のための整形）。

## 3. 影響範囲

- 表示するグラフの見た目・データ内容に変更はない（AlcoholAnalysisChartsのみ描画ライブラリが変わる）。
- Plotly化により、ホバー時のツールチップ表示や凡例配置が他ページと統一される。
- `fixedrange=True` により、対象グラフはユーザーによる拡大・縮小・パン操作ができなくなる。

## 4. 未対応・今後の検討事項

- `_monthly_avg_df` / `_stacked_monthly_bar` のような共通化を、他の分析クラス間でも
  横断的に整理できるか検討の余地あり。
