import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from src.components.charts.menu_analysis.ColorPalette import color_for_label
from src.components.charts.menu_analysis.PieUtils import (
    OTHER_LABEL,
    group_minor_slices,
    legend_hint_annotation,
    other_slice_legend_label,
)


class RamenAnalysisCharts:
    """昼・夜・深夜のラーメン分析グラフクラス"""

    TIME_COLORS = {
        "昼":   px.colors.qualitative.Pastel,
        "夜":   px.colors.qualitative.Set2,
        "深夜": px.colors.qualitative.Dark2,
    }
    WEEKDAY_ORDER = ["水", "木", "金", "土", "日"]
    WEEKDAY_MAP = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}


    # ──────────────────────────────────────────
    # ヘルパー：メニュー名リストから色リストを生成
    # ──────────────────────────────────────────
    def _get_menu_color_list(self, labels: list[str]) -> list[str]:
        """
        labels の順番に対応する色リストを返す（メニュー名ごとに決定的な色）。
        """
        return [color_for_label(label) for label in labels]

    # ──────────────────────────────────────────
    # 内部ヘルパー：月範囲フィルタ
    # ──────────────────────────────────────────
    def _filter_by_month_range(
        self,
        df: pd.DataFrame,
        month_start: str,   # 'YYYY_M'
        month_end:   str,   # 'YYYY_M'
    ) -> pd.DataFrame:
        """
        DataFrame のインデックス（日付）を month_start 〜 month_end の範囲で絞り込む。
        """
        if df.empty:
            return df

        # 範囲内のDataFrameを返すために、インデックスが日付でない場合は変換してから比較する
        work_df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(work_df.index):
            work_df.index = pd.to_datetime(work_df.index)

        # 'YYYY_M' → period('M') に変換して比較
        start_period = pd.Period(month_start.replace("_", "-"), freq="M")
        end_period   = pd.Period(month_end.replace("_", "-"),   freq="M")
        index_periods = work_df.index.to_period("M")

        # 指定月の行だけを抽出
        mask = (index_periods >= start_period) & (index_periods <= end_period)
        return work_df.loc[mask]
    
    # 文字列 'YYYY_M' を 'YYYY年M月' 形式に変換して、範囲表示も考慮したラベルを返す関数
    def _month_range_label(self, month_start: str, month_end: str) -> str:
        """'2024_4', '2024_6' → '2024年4月〜2024年6月' のような表示文字列を返す"""
        def fmt(m: str) -> str:
            y, mo = m.split("_")
            return f"{y}年{mo}月"
        return fmt(month_start) if month_start == month_end else f"{fmt(month_start)}〜{fmt(month_end)}"

    # ──────────────────────────────────────────
    # 1. 円グラフ：昼・夜・深夜ごとの提供割合
    # ──────────────────────────────────────────
    def pie_ramen_ratio_by_time(
        self,
        df_lunch:    pd.DataFrame,
        df_diner:    pd.DataFrame,
        df_midnight: pd.DataFrame,
        time_filter: str = "全体",
        month_start: str | None = None,
        month_end:   str | None = None,
        mode:  str = "販売数",
    ) -> None:
        datasets = {"昼": df_lunch, "夜": df_diner, "深夜": df_midnight}
        targets = datasets if time_filter == "全体" else {time_filter: datasets[time_filter]}

        # 月範囲フィルタ
        if month_start and month_end:
            targets = {
                label: self._filter_by_month_range(df, month_start, month_end)
                for label, df in targets.items()
            }

        # ── 全体の場合は3つを結合して1つのDataFrameに ──
        if time_filter == "全体":
            combined_df = pd.concat(targets.values())
            # 同じメニュー列が昼・夜・深夜で重複しているので列ごとに合算
            combined_df = combined_df.groupby(combined_df.index).sum()
            targets = {"全体": combined_df}

        n = len(targets)
        fig = make_subplots(
            rows=1, cols=n,
            specs=[[{"type": "pie"}] * n],
            vertical_spacing=0.1,
        )

        unit = "円" if mode == "売上" else "杯"
        for col_idx, (label, df) in enumerate(targets.items(), start=1):
            totals = df.sum(numeric_only=True)
            totals = totals[totals > 0]
            # 降順ソート
            totals = totals.sort_values(ascending=False)

            # 全体に占める割合が3%未満のスライスは「その他」に合算する
            # （隣接スライスの色が判別しにくくなる・凡例が埋まりすぎるのを防ぐ）
            other_legend_label = other_slice_legend_label(totals)
            grouped = group_minor_slices(totals)
            display_labels = grouped.index.tolist()
            values = grouped.values.tolist()
            # 凡例・ホバーには「その他」の中身を表示し、スライス上の文字は短いままにする
            legend_labels = [
                other_legend_label if lbl == OTHER_LABEL and other_legend_label else lbl
                for lbl in display_labels
            ]

            fig.add_trace(
                go.Pie(
                    labels=legend_labels,
                    values=values,
                    text=display_labels,
                    name=label,
                    textinfo="text+percent",
                    textfont=dict(size=11),
                    hovertemplate=f"%{{label}}<br>%{{value:,.0f}}{unit}<br>%{{percent}}<extra></extra>",
                    hole=0.3,
                    sort=False, # 割合順の自動並び替えをしない（「その他」を必ず最後にするため）
                    rotation=0, # 0度スタート
                    direction="clockwise",
                    insidetextorientation="horizontal", # テキストを水平に
                    # メニュー共通カラー
                    marker_colors=self._get_menu_color_list(display_labels),
                    # 円グラフ自体を上80%に収め、下20%をヒント表示用に空けておく
                    domain=dict(y=[0.22, 1]),
                ),
                row=1, col=col_idx,
            )

        # make_subplotsの自動domain割り当てで上のdomain指定が上書きされないよう、
        # トレース追加後に改めて明示する
        fig.update_traces(domain=dict(y=[0.22, 1]))

        range_str = self._month_range_label(month_start, month_end) if month_start and month_end else ""
        fig.update_layout(
            title_text=f"【{time_filter}】{range_str} ラーメン{mode}割合",
            margin=dict(l=20, r=20, t=100, b=90),
            height=720,
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), # 凡例を下へ
            annotations=[legend_hint_annotation(y=0.02)], # 円グラフ(上80%)と凡例(マイナス側)の間の空白に配置
        )
        st.plotly_chart(fig, use_container_width=True)

    # ──────────────────────────────────────────
    # 2. 棒グラフ：曜日ごとの各ラーメン提供杯数
    # ──────────────────────────────────────────
    def bar_ramen_by_weekday(
        self,
        df_lunch:    pd.DataFrame,
        df_diner:    pd.DataFrame,
        df_midnight: pd.DataFrame,
        time_filter: str = "全体",
        month_start: str | None = None,
        month_end:   str | None = None,
        mode: str = "販売数"
    ) -> None:
        datasets = {"昼": df_lunch, "夜": df_diner, "深夜": df_midnight}
        targets  = datasets if time_filter == "全体" else {time_filter: datasets[time_filter]}

        # 月範囲フィルタ
        if month_start and month_end:
            targets = {
                label: self._filter_by_month_range(df, month_start, month_end)
                for label, df in targets.items()
            }

         # ── 全体の場合は3つを結合して1つのDataFrameに ──
        if time_filter == "全体":
            combined_df = pd.concat(targets.values())
            combined_df = combined_df.groupby(combined_df.index).sum()
            targets = {"全体": combined_df}

        range_str = self._month_range_label(month_start, month_end) if month_start and month_end else ""

        if len(targets) == 1:
            label, df = next(iter(targets.items()))
            self._render_weekday_bar(df, label, range_str, mode)
        else:
            tabs = st.tabs(list(targets.keys()))
            for tab, (label, df) in zip(tabs, targets.items()):
                with tab:
                    self._render_weekday_bar(df, label, range_str, mode)

    # ──────────────────────────────────────────
    # 内部ヘルパー：棒グラフ描画
    # ──────────────────────────────────────────
    def _render_weekday_bar(self, df: pd.DataFrame, label: str, range_str: str , mode: str = "販売数") -> None:
        if df.empty:
            st.warning(f"{label}のデータがありません")
            return

        work_df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(work_df.index):
            work_df.index = pd.to_datetime(work_df.index)

        work_df["曜日"] = work_df.index.dayofweek.map(self.WEEKDAY_MAP)
        numeric_cols = work_df.select_dtypes(include="number").columns.tolist()
        weekday_df = (
            work_df.groupby("曜日")[numeric_cols]
            .sum()
            .reindex(self.WEEKDAY_ORDER)
            .fillna(0)
        )

        color_map = {col: color_for_label(col) for col in numeric_cols}

        unit = "円" if mode == "売上" else "杯"
        y_label = f"{mode}合計 ({unit})" # 軸のタイトル用

        fig = px.bar(
            weekday_df.reset_index(),
            x="曜日",
            y=numeric_cols,
            barmode="group",
            labels={"value": mode, "variable": "メニュー", "曜日": "曜日"},
            title=f"【{label}】{range_str} 曜日別ラーメン{mode}",
            color_discrete_map = color_map
        )
        fig.update_layout(
            xaxis=dict(title="曜日", categoryorder="array", categoryarray=self.WEEKDAY_ORDER, fixedrange=True),
            yaxis=dict(
                title=y_label,
                tickformat=",d" if mode == "売上" else None, # 売上の時だけカンマ区切り
                fixedrange=True,
            ),
            legend=dict(title="メニュー", orientation="v", x=1.02, y=0.5),
            margin=dict(l=20, r=20, t=80, b=40),
            height=450,
        )

        fig.update_traces(
            hovertemplate=f"曜日: %{{x}}<br>メニュー: %{{fullData.name}}<br>{mode}: %{{y:,.0f}}{unit}<extra></extra>"
        )

        st.plotly_chart(fig, use_container_width=True)