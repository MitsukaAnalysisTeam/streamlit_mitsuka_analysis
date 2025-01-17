import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

'''
グラフ生成用の関数を定義するファイル
'''
class DailyReportAnalysisCharts:
    def currency_formatter(self, 
                           x, 
                           _):
        return f'¥{int(x):,}'
    
    def customer_formatter(self, 
                        x, 
                        _):
        return f'{int(x):,}人'

    def lunch_night_stacked_bar(self, 
                                df, 
                                str1, 
                                str2, 
                                str3):
        fig, ax = plt.subplots(figsize=(20, 12))
        plt.bar(df.index, df[str1], align="center", color='darkorange', label=str1, width=0.5)
        plt.bar(df.index, df[str2], bottom=df[str1], align="center", color='royalblue', label=str2, width=0.5)
        plt.legend(loc="upper right", fontsize=10)
        ax.set_axisbelow(True)
        plt.xticks(rotation=90)
        if '売上' in str2:
            plt.yticks(np.arange(0, 370001, 25000),fontsize=15)
            plt.ylim(0, 370000)
            plt.axhline(y=200000, xmin=0, xmax=len(df.index), color='r')
            plt.axhline(y=100000, xmin=0, xmax=len(df.index), color='black')
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
        elif '客数' in str2:
            plt.yticks(np.arange(0, 201, 20),fontsize=15)
            plt.ylim(0, 200)
            plt.axhline(y=100, xmin=0, xmax=len(df.index), color='r')
        else:
            plt.ylim(0, 3000)
            plt.yticks(np.arange(0, 3001, 500),fontsize=15)
            plt.axhline(y=2000, xmin=0, xmax=len(df.index), color='r')
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
        ax.set(ylabel=str3)
        plt.xticks(np.arange(0, len(df), 1), df.index, rotation=28)
        plt.grid(axis='y')
        st.pyplot(fig)

    def daily_price_per_customer_bar(self,
                                     df
    ):
        fig, ax = plt.subplots(figsize=(15, 3))
        ax.set_axisbelow(True)
        plt.bar(np.arange(0,len(df),1),df["1日客単価"],width=0.5
                ,color="darkorange"
                )
        plt.ylim(0,3000)
        plt.yticks(np.arange(0,3001,500))
        plt.axhline (y=2000, xmin=0, xmax=len(df.index),color='r')
        plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
        plt.xticks(np.arange(0,len(df),1),df.index,rotation=28)
        plt.grid(axis='y')        
        st.pyplot(fig)

    def monthly_transfer_sum_bar(
            self,
            df_dic,
            str1
    ):
        sum = []
        x_labels = []
        fig, ax = plt.subplots(figsize=(20, 12))
        ax.set_axisbelow(True)
        # すべてのDataFrameにconvert_daily_report_dataを適用
        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    # DataFrameを変換
                    sum.append(df_dic[year][month][str1].sum())
                    x_labels.append(f"{year}/{month}({len(df_dic[year][month][str1])})")
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        sum_colors = ['#46bdc6']*(len(x_labels)-1)+['#ff6d01']
        plt.bar(x_labels,sum,color=sum_colors,width=0.5)
        plt.ticklabel_format(style='plain',axis='y')
        plt.xticks(rotation=20)
        plt.yticks(fontsize = 20)
        if "売上" in str1 or "客単価" in str1 :
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            plt.ylabel("月の総売上(円)")
        elif "客数" in str1:
            plt.ylabel("月の総客数(人)")
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
        plt.xlabel("年/月(営業日数)")
        plt.grid(axis='y', zorder=0)
        st.pyplot(fig)

    def monthly_transfer_mean_bar(
            self,
            df_dic,
            str1
    ):
        mean = []
        x_labels = []
        fig, ax = plt.subplots(figsize=(20, 12))
        ax.set_axisbelow(True)
        # すべてのDataFrameにconvert_daily_report_dataを適用
        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    # DataFrameを変換
                    mean.append(df_dic[year][month][str1].mean())
                    x_labels.append(f"{year}/{month}({len(df_dic[year][month][str1])})")
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        mean_colors = ['#46bdc6']*(len(x_labels)-1)+['#ff6d01']
        plt.bar(x_labels,mean,color=mean_colors,width=0.5)
        plt.ticklabel_format(style='plain',axis='y')
        plt.xticks(rotation=20)
        plt.yticks(fontsize = 20)
        if "売上" in str1:
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            plt.ylabel("月の総売上(円)")
        elif "客数" in str1:
            plt.ylabel("月の総客数(人)")
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
        plt.xlabel("年/月(営業日数)")
        plt.grid(axis='y', zorder=0)
        st.pyplot(fig)
        