import streamlit as st
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go


class LunchAnalysisCharts:
    def __init__(self):
        pass

    """
    def bar_ranking_df_by_month(
            self,
            df: pd.Series,
            date: str,
            fig_title: str
            ):
        year  = int(date[:4])
        month = int(date.split('_')[1])

        df_sorted = df.sort_values(ascending=False)

        # SeriesをDataFrameに変換してから渡す
        df_plot = df_sorted.reset_index()
        df_plot.columns = ["商品", "販売数"]

        color_map = {0: '#FFD700', 1: '#C0C0C0', 2: '#CD7F32'}
        df_plot["color"] = [
            color_map.get(i, '#4169E1') for i in range(len(df_plot))
        ]

        fig = px.bar(
            df_plot,
            x="商品",
            y="販売数",
            title=f"{year}年{month}月 の {fig_title}",
            color="color",
            color_discrete_map="identity",
        )
        fig.update_layout(
            xaxis=dict(title=''),
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=80),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    def line_trend_df(
            self,
            df: pd.DataFrame,
            fig_title: str
            ):
        # plotlyでグラフ作成
        fig = px.line(
            df,
            x=df.index,
            y=df.columns,
            labels={"x": "日付", "value": "販売数", "variable": "商品"},
            title=f"{fig_title} の販売数推移"
        )

        fig.update_layout(
            xaxis=dict(title=''),
            margin=dict(l=20, r=20, t=40, b=80)
        )
    """

    def pie_lunch_category(
        self,
        df_dict: dict,         # json_to_df_dict の結果
        selected_month: str,   # "YYYY_M" 形式
    ) -> None:
        """
        円グラフ①：昼カテゴリ別提供数
        ラーメン系各メニュー・発酵唐揚げプレート・発酵御膳・キッズの割合
        """
        TARGET_KEYS = [
            "カリー", "カリーつけ麺", "海老みそ", "焦がし海老味噌",
            "ベジ味噌", "白味噌", "温玉カレーラーメン", "油そば",
            "発酵唐揚げプレート", "発酵御膳", "キッズ"
        ]

        year  = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_key(key: str) -> float:
            if key not in df_dict:
                return 0.0
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)
            df = df[(df.index.year == year) & (df.index.month == month)]
            return float(pd.to_numeric(df.values.flatten(), errors='coerce').sum())

        # キーごとに合計を算出してSeriesに変換
        totals = pd.Series(
            {key: _sum_key(key) for key in TARGET_KEYS}
        )
        totals = totals[totals > 0]  # 0件除外

        if totals.empty:
            st.warning("該当月のデータがありません")
            return

        fig = go.Figure(go.Pie(
            labels=totals.index.tolist(),   # list に明示変換
            values=totals.values.tolist(),  # list に明示変換
            textinfo="label+percent",
            hole=0.3,
            marker_colors=px.colors.qualitative.Pastel,
        ))
        fig.update_layout(
            title_text=f"{year}年{month}月 昼カテゴリ別提供数",
            title_font_size=16,
            margin=dict(l=20, r=20, t=60, b=20),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    def pie_set_menu(
        self,
        df_dict: dict,
        selected_month: str,
    ) -> None:
        """
        円グラフ②：セットメニュー内訳（提供数）
        セット・ラーメンセットキーの内訳をそのまま集計
        """
        SET_KEYS = ["セット", "ラーメンセット"]

        year  = int(selected_month[:4])
        month = int(selected_month.split('_')[1])

        def _sum_by_item(key: str) -> pd.Series:
            """キー内の各商品ごとの合計を返す"""
            if key not in df_dict:
                return pd.Series(dtype=float)
            df = df_dict[key].copy()
            if not pd.api.types.is_datetime64_any_dtype(df.index):
                df.index = pd.to_datetime(df.index)
            df = df[(df.index.year == year) & (df.index.month == month)]
            df = df.apply(pd.to_numeric, errors='coerce')
            return df.sum()

        combined = pd.concat(
            [_sum_by_item(k) for k in SET_KEYS]
        ).fillna(0)
        combined = combined[combined > 0]  # 0件除外

        if combined.empty:
            st.warning("該当月のセットデータがありません")
            return

        fig = go.Figure(go.Pie(
            labels=combined.index.tolist(),
            values=combined.values.tolist(),
            textinfo="label+percent",
            hole=0.3,
            marker_colors=px.colors.qualitative.Set2,
        ))
        fig.update_layout(
            title_text=f"{year}年{month}月 セットメニュー内訳",
            title_font_size=16,
            margin=dict(l=20, r=20, t=60, b=20),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)