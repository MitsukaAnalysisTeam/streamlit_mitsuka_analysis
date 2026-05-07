import streamlit as st
import numpy as np
import plotly.graph_objects as go

'''
グラフ生成用の関数を定義するファイル
'''
class DailyReportAnalysisCharts:
    '''
    日報分析クラス用の画像生成クラス
    '''

    def _stacked_hover_suffix(self, str2: str) -> str:
        if '売上' in str2:
            return '¥%{y:,.0f}'
        if '客数' in str2:
            return '%{y:,.0f}人'
        return '¥%{y:,.0f}'

    def lunch_night_stacked_bar(self,
                                df,
                                str1,
                                str2,
                                str3):
        x_vals = [str(i) for i in df.index]
        ht_suffix = self._stacked_hover_suffix(str2)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_vals,
            y=df[str1].tolist(),
            name=str1,
            marker_color='darkorange',
            hovertemplate=f'日: %{{x}}<br>{str1}: {ht_suffix}<extra></extra>',
        ))
        fig.add_trace(go.Bar(
            x=x_vals,
            y=df[str2].tolist(),
            name=str2,
            marker_color='royalblue',
            hovertemplate=f'日: %{{x}}<br>{str2}: {ht_suffix}<extra></extra>',
        ))

        if '売上' in str2:
            y_max = 370000
            tick_vals = list(np.arange(0, 370001, 25000))
            fig.add_hline(y=200000, line_color='red', line_width=1)
            fig.add_hline(y=100000, line_color='black', line_width=1)
            y_tickformat = ',.0f'
            y_tickprefix = '¥'
        elif '客数' in str2:
            y_max = 200
            tick_vals = list(np.arange(0, 201, 20))
            fig.add_hline(y=100, line_color='red', line_width=1)
            y_tickformat = ',.0f'
            y_tickprefix = ''
        else:
            y_max = 3000
            tick_vals = list(np.arange(0, 3001, 500))
            fig.add_hline(y=2000, line_color='red', line_width=1)
            y_tickformat = ',.0f'
            y_tickprefix = '¥'

        fig.update_layout(
            barmode='stack',
            yaxis=dict(
                title=str3,
                range=[0, y_max],
                tickmode='array',
                tickvals=tick_vals,
                tickformat=y_tickformat,
                tickprefix=y_tickprefix,
                showgrid=True,
                gridcolor='#e0e0e0',
            ),
            xaxis=dict(
                title='日',
                tickangle=-28,
                type='category',
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
            margin=dict(l=40, r=20, t=60, b=80),
            height=520,
        )
        st.plotly_chart(fig, use_container_width=True)

    def daily_price_per_customer_bar(self,
                                     df
    ):
        x_vals = [str(i) for i in df.index]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_vals,
            y=df["1日客単価"].tolist(),
            name='1日客単価',
            marker_color='darkorange',
            hovertemplate='日: %{x}<br>客単価: ¥%{y:,.0f}<extra></extra>',
        ))
        fig.add_hline(y=2000, line_color='red', line_width=1)
        fig.update_layout(
            yaxis=dict(
                title='客単価 (¥)',
                range=[0, 3000],
                tickmode='array',
                tickvals=list(np.arange(0, 3001, 500)),
                tickformat=',.0f',
                tickprefix='¥',
                showgrid=True,
                gridcolor='#e0e0e0',
            ),
            xaxis=dict(
                title='日',
                tickangle=-28,
                type='category',
            ),
            showlegend=True,
            legend=dict(orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom'),
            hovermode='x unified',
            plot_bgcolor='white',
            margin=dict(l=40, r=20, t=60, b=80),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)

    def monthly_transfer_sum_bar(
            self,
            df_dic,
            str1
    ):
        sum_vals = []
        x_labels = []
        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    sum_vals.append(df_dic[year][month][str1].sum())
                    x_labels.append(f"{year}/{month}({len(df_dic[year][month][str1])})")
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        sum_colors = ['#46bdc6'] * (len(x_labels) - 1) + ['#ff6d01']

        is_currency = "売上" in str1 or "客単価" in str1
        if is_currency:
            y_title = "月の総売上(円)"
            hover_tmpl = '年月: %{x}<br>合計: ¥%{y:,.0f}<extra></extra>'
            y_tickprefix = '¥'
        else:
            y_title = "月の総客数(人)"
            hover_tmpl = '年月: %{x}<br>合計: %{y:,.0f}人<extra></extra>'
            y_tickprefix = ''

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_labels,
            y=sum_vals,
            name=str1,
            marker_color=sum_colors,
            hovertemplate=hover_tmpl,
        ))
        fig.update_layout(
            xaxis=dict(title="年/月(営業日数)", tickangle=-90, tickfont=dict(size=14)),
            yaxis=dict(
                title=y_title,
                tickformat=',.0f',
                tickprefix=y_tickprefix,
                tickfont=dict(size=14),
                showgrid=True,
                gridcolor='#e0e0e0',
            ),
            showlegend=True,
            legend=dict(orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom'),
            hovermode='x unified',
            plot_bgcolor='white',
            margin=dict(l=60, r=20, t=60, b=120),
            height=560,
        )
        st.plotly_chart(fig, use_container_width=True)

    def monthly_transfer_mean_bar(
            self,
            df_dic,
            str1
    ):
        mean_vals = []
        x_labels = []
        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    mean_vals.append(df_dic[year][month][str1].mean())
                    x_labels.append(f"{year}/{month}({len(df_dic[year][month][str1])})")
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        mean_colors = ['#46bdc6'] * (len(x_labels) - 1) + ['#ff6d01']

        is_currency = "売上" in str1 or "客単価" in str1
        if is_currency:
            y_title = "月の総売上(円)"
            hover_tmpl = '年月: %{x}<br>平均: ¥%{y:,.1f}<extra></extra>'
            y_tickprefix = '¥'
        else:
            y_title = "月の総客数(人)"
            hover_tmpl = '年月: %{x}<br>平均: %{y:,.1f}人<extra></extra>'
            y_tickprefix = ''

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_labels,
            y=mean_vals,
            name=str1,
            marker_color=mean_colors,
            hovertemplate=hover_tmpl,
        ))
        fig.update_layout(
            xaxis=dict(title="年/月(営業日数)", tickangle=-90, tickfont=dict(size=14)),
            yaxis=dict(
                title=y_title,
                tickformat=',.1f',
                tickprefix=y_tickprefix,
                tickfont=dict(size=14),
                showgrid=True,
                gridcolor='#e0e0e0',
            ),
            showlegend=True,
            legend=dict(orientation='h', y=1.02, x=1, xanchor='right', yanchor='bottom'),
            hovermode='x unified',
            plot_bgcolor='white',
            margin=dict(l=60, r=20, t=60, b=120),
            height=560,
        )
        st.plotly_chart(fig, use_container_width=True)


    def weekly_comparison_bar(self, df1, df2, str1: str, date1: str, date2: str):
        # グラフの作成
        fig = go.Figure()

        # df1 用の棒グラフ (色: #46bdc6)
        fig.add_trace(go.Bar(
            x=df1.index,
            y=df1[str1],
            name=f"{date1[:4]}年{date1[5:]}月",  # 月のラベル
            marker_color="#46bdc6",
            width=0.1,
            offsetgroup=1  # バーをグループ化
        ))

        # df2 用の棒グラフ (色: #ff6d01)
        fig.add_trace(go.Bar(
            x=df2.index,
            y=df2[str1],
            name=f"{date2[:4]}年{date2[5:]}月",  # 月のラベル
            marker_color="#ff6d01",
            width=0.1,
            offsetgroup=2  # バーをグループ化
        ))

        yaxis_extra = {}
        if "売上" in str1 or "客単価" in str1:
            yaxis_extra = dict(tickprefix='¥', tickformat=',.0f', title="月の総売上(円)")
        elif "客数" in str1:
            yaxis_extra = dict(tickformat=',.0f', ticksuffix='人', title="月の総客数(人)")

        fig.update_layout(
            xaxis=dict(
                title="日付",
                tickvals=np.arange(0, len(df1.index), 1),
                ticktext=df1.index.tolist(),
                tickfont=dict(size=15),
            ),
            yaxis=dict(tickfont=dict(size=15), **yaxis_extra),
            title=f'{date1}と{date2}の{str1}の曜日別比較',
            barmode='group',
            showlegend=True,
            legend=dict(
                title="月",
                font=dict(size=18),
                x=0.01,
                y=0.99
            ),
            margin=dict(l=40, r=40, t=40, b=80),
            plot_bgcolor='white',
            hovermode='x unified',
        )

        # Streamlit でグラフを表示
        st.plotly_chart(fig, use_container_width=True)
