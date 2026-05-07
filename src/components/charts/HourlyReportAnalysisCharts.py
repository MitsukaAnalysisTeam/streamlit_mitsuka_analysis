import streamlit as st
import plotly.graph_objects as go


class HourlyReportAnalysisCharts:

    def __init__(self):

        self.time_dic = ['11時','12時','13時','14時','15時','16時','17時','18時','19時','20時','21時','22時','23時']
        self.color_day_dic = {'水':'royalblue','木':'lime','金':'gold','土':'brown','日':'orangered'}

    def _week_hourly_figure(self, filtered_df, label, height: int = 420):
        """
        filtered_df: 行=曜日、列=時間帯 の平均データ
        """
        plot_df = filtered_df.T.iloc[0:len(self.time_dic), :]
        hours = plot_df.index.tolist()
        fig = go.Figure()
        for day in plot_df.columns:
            color = self.color_day_dic.get(str(day), '#888888')
            y_vals = plot_df[day].tolist()
            if "売上" in label or "客単価" in label:
                hovertemplate = f'時間: %{{x}}<br>{day}: ¥%{{y:,.0f}}<extra>{day}</extra>'
            else:
                hovertemplate = f'時間: %{{x}}<br>{day}: %{{y:,.1f}}人<extra>{day}</extra>'
            fig.add_trace(go.Bar(
                name=str(day),
                x=hours,
                y=y_vals,
                marker_color=color,
                marker_line_color='black',
                marker_line_width=1,
                hovertemplate=hovertemplate,
            ))

        if "売上" in label or "客単価" in label:
            yaxis_cfg = dict(
                title=label,
                range=[0, 35000],
                tickformat=',.0f',
                tickprefix='¥',
                showgrid=True,
                gridcolor='#e0e0e0',
            )
        else:
            yaxis_cfg = dict(
                title=label,
                range=[0, 30],
                tickformat='.1f',
                ticksuffix='人',
                showgrid=True,
                gridcolor='#e0e0e0',
            )

        fig.update_layout(
            barmode='group',
            xaxis=dict(title='', tickfont=dict(size=14)),
            yaxis=yaxis_cfg,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(size=11),
            ),
            hovermode='x unified',
            plot_bgcolor='white',
            margin=dict(l=50, r=20, t=70, b=50),
            height=height,
        )
        return fig

    def week_comp_bar(self, df_week, label, selected_days):
        """
        指定された曜日のデータのみを表示する棒グラフを作成

        Parameters:
        -----------
        df_week : DataFrame
            曜日ごとの時間別データ
        label : str
            グラフのラベル
        selected_days : str
            表示する曜日のリスト。Noneの場合は全ての曜日を表示
        """
        if selected_days is None or selected_days == "全体":
            filtered_df = df_week
        else:
            filtered_df = df_week.loc[[selected_days]]

        if filtered_df.empty:
            st.warning("選択された曜日のデータがありません。")
            return

        fig = self._week_hourly_figure(filtered_df, label)
        st.plotly_chart(fig, use_container_width=True)

    def compare_two_data(self, df1, df2, label, title1, title2, selected_days1=None, selected_days2=None):
        """
        2つのデータを横に並べて比較するグラフを作成
        """
        cols = st.columns(2)

        with cols[0]:
            st.write(f"**{title1}**")
            if df1 is not None and not df1.empty:
                if selected_days1 is None or selected_days1 == "全体":
                    filtered_df1 = df1
                else:
                    try:
                        filtered_df1 = df1.loc[[selected_days1]] if isinstance(selected_days1, str) else df1.loc[selected_days1]
                    except KeyError:
                        st.warning(f"選択された曜日 '{selected_days1}' のデータがありません。")
                        return

                if not filtered_df1.empty:
                    fig1 = self._week_hourly_figure(filtered_df1, label, height=380)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.warning("表示するデータがありません。")
            else:
                st.warning("データが存在しません。")

        with cols[1]:
            st.write(f"**{title2}**")
            if df2 is not None and not df2.empty:
                if selected_days2 is None or selected_days2 == "全体":
                    filtered_df2 = df2
                else:
                    try:
                        filtered_df2 = df2.loc[[selected_days2]] if isinstance(selected_days2, str) else df2.loc[selected_days2]
                    except KeyError:
                        st.warning(f"選択された曜日 '{selected_days2}' のデータがありません。")
                        return

                if not filtered_df2.empty:
                    fig2 = self._week_hourly_figure(filtered_df2, label, height=380)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.warning("表示するデータがありません。")
            else:
                st.warning("データが存在しません。")
