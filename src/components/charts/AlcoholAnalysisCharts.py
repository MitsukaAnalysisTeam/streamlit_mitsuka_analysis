import streamlit as st
import plotly.graph_objects as go
import pandas as pd


class AlcoholAnalysisCharts:

    def _monthly_avg_df(self, data: pd.DataFrame, cols: list) -> pd.DataFrame:
        data = data.copy()
        data["日付"] = pd.to_datetime(data["日付"], format='mixed')
        data.set_index("日付", inplace=True)

        monthly_sum = data.resample('M')[cols].sum()
        business_days = data.resample('M')[cols].count()
        monthly_avg = monthly_sum / business_days
        monthly_avg.index = monthly_avg.index.to_series().dt.strftime('%Y_%m')
        return monthly_avg

    def _stacked_monthly_bar(self, monthly_avg: pd.DataFrame, colors: list, title: str) -> go.Figure:
        x_vals = monthly_avg.index.tolist()
        fig = go.Figure()
        for col, color in zip(monthly_avg.columns, colors):
            fig.add_trace(go.Bar(
                x=x_vals,
                y=monthly_avg[col].tolist(),
                name=col,
                marker_color=color,
                hovertemplate=f'年月: %{{x}}<br>{col}: %{{y:,.1f}}<extra></extra>',
            ))
        fig.update_layout(
            title_text=title,
            barmode='stack',
            xaxis=dict(title='年月', tickangle=-45, fixedrange=True),
            yaxis=dict(
                title='1日平均',
                tickformat=',.1f',
                showgrid=True,
                gridcolor='#e0e0e0',
                fixedrange=True,
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            margin=dict(l=50, r=20, t=60, b=100),
            height=480,
        )
        return fig

    def wine_graph(self, data):
        monthly_avg = self._monthly_avg_df(data, ["一升瓶ワイン", "ボトルワイン"])
        fig = self._stacked_monthly_bar(monthly_avg, ["pink", "red"], "月毎の1日合計売上の推移")
        st.plotly_chart(fig, use_container_width=True)

    def akishika_graph(self, data):
        cols = ["秋鹿", "ハイボール", "りんごカクテル", "りんごと熱燗", "梅酒", "敷島"]
        monthly_avg = self._monthly_avg_df(data, cols)
        colors = ["orange", "gold", "darkblue", "tomato", "limegreen", "purple"]
        fig = self._stacked_monthly_bar(monthly_avg, colors, "月毎の1日合計売上・杯数の推移")
        st.plotly_chart(fig, use_container_width=True)

    def beer_graph(self, data):
        cols = ["ドラフト", "リアル", "ボトル", "ハッピーアワー", "オリゼ", "ビール祭り", "スタッフ"]
        monthly_avg = self._monthly_avg_df(data, cols)
        colors = ["orange", "darkblue", "forestgreen", "darkkhaki", "brown", "pink", "dimgrey"]
        fig = self._stacked_monthly_bar(monthly_avg, colors, "月毎の1日合計売上の推移")
        st.plotly_chart(fig, use_container_width=True)

    def alchol_graph(self, data):
        cols = ["ビール", "秋鹿", "ワイン"]
        monthly_avg = self._monthly_avg_df(data, cols)
        colors = ["orange", "yellow", "purple"]
        fig = self._stacked_monthly_bar(monthly_avg, colors, "月毎の1日合計売上の推移")
        st.plotly_chart(fig, use_container_width=True)
