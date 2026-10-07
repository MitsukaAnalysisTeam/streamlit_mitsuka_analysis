import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from src.components.charts.menu_analysis.ColorPalette import colors_for_labels


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

    def _graph_from_data(self, data: pd.DataFrame, title: str) -> None:
        """dataの'日付'以外の列をそのままグラフの対象カテゴリとして描画する。

        対象カテゴリの一覧はmenu.json側(flag)で決まるため、ここでは
        dataに既に絞り込まれている列をそのまま使うだけで、カテゴリ名を
        コード側に持たない。
        """
        cols = [c for c in data.columns if c != "日付"]
        monthly_avg = self._monthly_avg_df(data, cols)
        colors = colors_for_labels(cols)
        fig = self._stacked_monthly_bar(monthly_avg, colors, title)
        st.plotly_chart(fig, use_container_width=True)

    def wine_graph(self, data):
        self._graph_from_data(data, "月毎の1日合計売上の推移")

    def akishika_graph(self, data):
        self._graph_from_data(data, "月毎の1日合計売上・杯数の推移")

    def beer_graph(self, data):
        self._graph_from_data(data, "月毎の1日合計売上の推移")

    def alchol_graph(self, data):
        self._graph_from_data(data, "月毎の1日合計売上の推移")
