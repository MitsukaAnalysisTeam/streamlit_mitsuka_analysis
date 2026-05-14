import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class RamenAnalysisCharts:
    """昼・夜・深夜のラーメン分析グラフクラス"""

    # ──────────────────────────────────────────
    # メニュー共通カラーマップ
    # ──────────────────────────────────────────
    MENU_COLORS = {
        # 味噌系
        "白味噌":           "#C8A882",   # 濃い肌色
        "赤味噌":           "#8B1A1A",   # 濃い赤
        "辛味噌":           "#CC2200",   # 辛そうな赤
        "焦がし味噌北海道": "#FFD700",   # 明るい黄色
        "ベジ味噌":         "#6B8E6B",   # 草色（野菜）
        "あさりと味噌":     "#7BA7BC",   # 青みがかった色（あさり）
        # つけ麺系
        "つけ麺8号":        "#4682B4",   # スチールブルー
        "つけ麺6号":        "#C04000",   # 辛そうな赤
        "カリーつけ麺":     "#E0B870",   # やや黄みがかった肌色
        # カリー・海老系
        "カリー":           "#C8860A",   # カレー色
        "海老味噌カリー":   "#B06020",   # 海老味噌カリー
        "担々麺":           "#C04000",   # 担々麺（橙赤）
        "TOYONO":           "#9B7BB8",   # 紫系（独自色）
        "イカスミ":         "#2C2C2C",   # 黒
        "油そば":           "#5C3A1E",   # 醤油色（茶）
        "和え玉":           "#32CD32",   # ライムグリーン
        # 昼ランチ系
        "海老みそ":         "#D4785A",   # 海老みそ（淡い海老色）
        "焦がし海老味噌":   "#A0522D",   # 焦がし感（茶系）
        "温玉カレーラーメン":"#D4A820",  # カレー黄
        "シビ辛丼":         "#B03000",   # 辛そうな橙赤
    }
    # カラーマップにないメニューへのフォールバック用パレット
    _FALLBACK_COLORS = px.colors.qualitative.Pastel

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
        labels の順番に対応する色リストを返す。
        MENU_COLORS に定義がないメニューはフォールバックパレットから順番に割り当てる。
        """
        colors = []
        fallback_idx = 0
        for label in labels:
            if label in self.MENU_COLORS:
                colors.append(self.MENU_COLORS[label])
            else:
                colors.append(self._FALLBACK_COLORS[fallback_idx % len(self._FALLBACK_COLORS)])
                fallback_idx += 1
        return colors

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

            # 全体に占める割合が3%未満のスライスはラベルを非表示にしてlegendに逃がす
            total_sum = totals.sum()
            threshold = 0.03

            visible_labels = [
                lbl if (val / total_sum) >= threshold else ""
                for lbl, val in zip(totals.index.tolist(), totals.values.tolist())
            ]

            fig.add_trace(
                go.Pie(
                    labels=totals.index.tolist(),
                    values=totals.values.tolist(),
                    name=label,
                    text=visible_labels,   
                    textinfo="text+percent",
                    hovertemplate=f"%{{label}}<br>%{{value:,.0f}}{unit}<br>%{{percent}}<extra></extra>",
                    hole=0.3,
                    rotation=0, # 0度スタート
                    direction="clockwise",
                    insidetextorientation="horizontal", # テキストを水平に
                    # メニュー共通カラー
                    marker_colors=self._get_menu_color_list(totals.index.tolist()),
                ),
                row=1, col=col_idx,
            )
            
        range_str = self._month_range_label(month_start, month_end) if month_start and month_end else ""
        fig.update_layout(
            title_text=f"【{time_filter}】{range_str} ラーメン{mode}割合",
            margin=dict(l=20, r=20, t=130, b=80),
            height=550,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5) # 凡例を下へ
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

        color_map = {col: self.MENU_COLORS.get(col, self._FALLBACK_COLORS[i % len(self._FALLBACK_COLORS)])
                     for i, col in enumerate(numeric_cols)}

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
            xaxis=dict(title="曜日", categoryorder="array", categoryarray=self.WEEKDAY_ORDER),
            yaxis=dict(
                title=y_label,
                tickformat=",d" if mode == "売上" else None # 売上の時だけカンマ区切り
            ),
            legend=dict(title="メニュー", orientation="v", x=1.02, y=0.5),
            margin=dict(l=20, r=20, t=80, b=40),
            height=450,
        )

        fig.update_traces(
            hovertemplate=f"曜日: %{{x}}<br>メニュー: %{{fullData.name}}<br>{mode}: %{{y:,.0f}}{unit}<extra></extra>"
        )

        st.plotly_chart(fig, use_container_width=True)