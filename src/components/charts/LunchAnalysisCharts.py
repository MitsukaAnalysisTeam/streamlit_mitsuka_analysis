import streamlit as st
import plotly.express as px
import pandas as pd


class LunchAnalysisCharts:
    def __init__(self):
        pass


    def bar_ranking_df_by_month(
            self,
            df: pd.DataFrame,
            date: str,
            fig_title: str
            ):
        """
        指定された年月の各商品の合計販売数をStreamlitで可視化する関数（Plotly版）
        - df: データフレーム (インデックスが日付)
        - date: 'YYYY_MM' 形式の文字列
        """
        year = int(date[:4])
        month = int(date.split('_')[1])        # データを販売数の降順に並べ替え
        df_sorted = df.sort_values(ascending=False)

        # 商品の順位に基づいて色を設定
        color_map = {
            0: '#FFD700',   # 1位: Gold
            1: '#C0C0C0',   # 2位: Silver
            2: '#CD7F32',   # 3位: Bronze
        }

        # その他の商品は青色
        colors = [color_map.get(i, 'blue') for i in range(len(df_sorted))]

        # plotlyでグラフ作成
        fig = px.bar(
            df_sorted,
            x=df_sorted.index,
            y=df_sorted.values,
            labels={"x": "商品", "y": "販売数"},
            title=f"{year}年{month}月 の {fig_title}",
            color=colors,  # 色を設定
            color_discrete_map='identity'  # カスタム色を適用
        )

        fig.update_layout(
            xaxis=dict(title=''),
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=80)
        )

        st.plotly_chart(fig, use_container_width=True)

    def line_trend_df(
            self,
            df: pd.DataFrame,
            fig_title: str
            ):
        """
        指定されたデータフレームの各商品の販売数の推移をStreamlitで可視化する関数（Plotly版）
        - df: データフレーム (インデックスが日付)
        """
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

        st.plotly_chart(fig, use_container_width=True)