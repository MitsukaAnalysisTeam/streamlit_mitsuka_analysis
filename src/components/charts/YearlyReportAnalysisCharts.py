import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


class YearlyReportAnalysisCharts:
    def currency_formatter(self, x, _):
        return f"¥{int(x):,}"

    def customer_formatter(self, x, _):
        return f"{int(x):,}人"

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

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.set_axisbelow(True)

        x_labels = df_yearly.index.astype(str).tolist()
        colors = ["#46bdc6"] * len(x_labels)
        colors[-1] = "#ff6d01"

        ax.bar(x_labels, df_yearly[metric_col], color=colors, width=0.6)
        ax.grid(axis="y")
        ax.set_xlabel("年")
        ax.set_ylabel(y_label)

        if currency:
            ax.yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
        elif people:
            ax.yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))

        st.pyplot(fig)
