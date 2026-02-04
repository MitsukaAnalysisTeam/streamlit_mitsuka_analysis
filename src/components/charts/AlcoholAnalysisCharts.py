import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import plotly.graph_objects as go
import pandas as pd

class AlcoholAnalysisCharts:
    def wine_graph(self, data):
        data["日付"] = pd.to_datetime(data["日付"], format='mixed')
        data.set_index("日付", inplace=True)

        monthly_sum = data.resample('M')[["一升瓶ワイン", "ボトルワイン"]].sum()

        business_days = data.resample('M')[["一升瓶ワイン", "ボトルワイン"]].count()
        monthly_avg = monthly_sum / business_days

        monthly_avg.index = monthly_avg.index.to_series().dt.strftime('%Y_%m')

        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_avg.plot(kind='bar', stacked=True, ax=ax, color=["pink", "red"])

        ax.set_title("月毎の1日合計売上の推移", fontsize=18)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0,), borderaxespad=0)
        plt.xticks(rotation=45)

        st.pyplot(fig)

    def akishika_graph(self, data):
        data["日付"] = pd.to_datetime(data["日付"], format='mixed')
        data.set_index("日付", inplace=True)

        monthly_sum = data.resample('M')[["秋鹿", "ハイボール", "りんごカクテル", "りんごと熱燗", "梅酒", "敷島"]].sum()

        business_days = data.resample('M')[["秋鹿", "ハイボール", "りんごカクテル", "りんごと熱燗", "梅酒", "敷島"]].count()
        monthly_avg = monthly_sum / business_days

        monthly_avg.index = monthly_avg.index.to_series().dt.strftime('%Y_%m')

        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_avg.plot(kind='bar', stacked=True, ax=ax, color=["orange", "gold", "darkblue", "tomato", "limegreen", "purple"])


        ax.set_title("月毎の1日合計売上・客数の推移", fontsize=18)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0,), borderaxespad=0)
        plt.xticks(rotation=45)

        st.pyplot(fig)

    def beer_graph(self, data):
        data["日付"] = pd.to_datetime(data["日付"], format='mixed')
        data.set_index("日付", inplace=True)

        monthly_sum = data.resample('M')[["ドラフト", "リアル", "ボトル", "ハッピーアワー","オリゼ", "ビール祭り", "スタッフ" ]].sum()

        business_days = data.resample('M')[["ドラフト", "リアル", "ボトル", "ハッピーアワー","オリゼ", "ビール祭り", "スタッフ"]].count()
        monthly_avg = monthly_sum / business_days

        monthly_avg.index = monthly_avg.index.to_series().dt.strftime('%Y_%m')

        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_avg.plot(kind='bar', stacked=True, ax=ax, color=["orange", "darkblue", "forestgreen", "darkkhaki", "brown", "pink", "dimgrey"])

        ax.set_title("月毎の1日合計売上の推移", fontsize=18)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0,), borderaxespad=0)
        plt.xticks(rotation=45)

        st.pyplot(fig)

    def alchol_graph(self, data):
        data["日付"] = pd.to_datetime(data["日付"], format='mixed')
        data.set_index("日付", inplace=True)

        monthly_sum = data.resample('M')[["ビール", "秋鹿", "ワイン"]].sum()

        business_days = data.resample('M')[["ビール", "秋鹿", "ワイン"]].count()
        monthly_avg = monthly_sum / business_days

        monthly_avg.index = monthly_avg.index.to_series().dt.strftime('%Y_%m')

        fig, ax = plt.subplots(figsize=(12, 6))
        monthly_avg.plot(kind='bar', stacked=True, ax=ax, color=["orange", "yellow", "purple"])

        ax.set_title("月毎の1日合計売上の推移", fontsize=18)
        ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0,), borderaxespad=0)
        plt.xticks(rotation=45)

        st.pyplot(fig)