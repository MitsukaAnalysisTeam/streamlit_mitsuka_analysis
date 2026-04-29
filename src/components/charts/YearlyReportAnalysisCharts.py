import streamlit as st
import plotly.graph_objects as go


class YearlyReportAnalysisCharts:
    def _format_value_text(self, value, currency: bool, people: bool) -> str:
        if currency:
            return f"¥{value:,.0f}"
        if people:
            return f"{value:,.0f}人"
        return f"{value:,.1f}"

    def plot_yearly_bar(
        self,
        df_yearly,
        metric_col: str,
        y_label: str,
        currency: bool = False,
        people: bool = False,
    ):
        if df_yearly.empty or metric_col not in df_yearly.columns:
            st.warning(f"{metric_col} のデータが存在しません。")
            return

        x_labels = df_yearly.index.astype(str).tolist()
        colors = ["#46bdc6"] * len(x_labels)
        colors[-1] = "#ff6d01"
        y_values = df_yearly[metric_col].astype(float)
        text_values = [self._format_value_text(v, currency, people) for v in y_values]

        hover_format = ",.0f"
        hover_suffix = ""
        if currency:
            hover_prefix = "¥"
        else:
            hover_prefix = ""
            if people:
                hover_suffix = "人"

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=x_labels,
                y=y_values,
                name=metric_col,
                marker_color=colors,
                text=text_values,
                textposition="outside",
                texttemplate="<b>%{text}</b>",
                textfont=dict(size=13, color="#1f1f1f"),
                cliponaxis=False,
                hovertemplate=f"年: %{{x}}<br>{metric_col}: {hover_prefix}%{{y:{hover_format}}}{hover_suffix}<extra>{metric_col}</extra>",
                showlegend=True,
            )
        )

        fig.update_layout(
            xaxis_title="年",
            yaxis_title=y_label,
            yaxis=dict(tickformat=","),
            margin=dict(l=40, r=20, t=40, b=40),
            plot_bgcolor="white",
            height=420,
        )
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#e9ecef")

        st.plotly_chart(fig, use_container_width=True)
