import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np



class HourlyReportAnalysisCharts:

    def __init__(self):

        self.time_dic = ['11時','12時','13時','14時','15時','16時','17時','18時','19時','20時','21時','22時','23時']
        self.color_day_dic = {'水':'royalblue','木':'lime','金':'gold','土':'brown','日':'orangered'}

    def currency_formatter(self, 
                           x, 
                           _):
        return f'¥{int(x):,}'
    
    def customer_formatter(self, 
                        x, 
                        _):
        return f'{int(x):,}人'
        
    def week_comp_bar(self, df_week, label):
        # 転置して時間データを取り出し、棒グラフを作成
        fig, ax = plt.subplots(figsize=(15, 5))
        df_week.T.iloc[0:len(self.time_dic), :].plot.bar(
            ax=ax,
            width=0.8,
            color=self.color_day_dic,
            edgecolor='black',
            linewidth=1
        )

        # 軸ラベルの設定
        if "売上" in label or "客単価" in label:
            ax.yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            ax.set_ylabel("月の総売上(円)", fontsize=15)
        elif "客数" in label:
            ax.set_ylabel("月の総客数(人)", fontsize=15)
            ax.yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))

        # 軸のフォントサイズ設定
        ax.tick_params(axis='x', labelsize=15, rotation=0)
        ax.tick_params(axis='y', labelsize=15)

        # グリッドとラベル
        ax.set_ylabel(label)
        ax.legend(fontsize=9, loc='upper right')
        ax.grid()

        # グラフをStreamlitで表示
        st.pyplot(fig)

