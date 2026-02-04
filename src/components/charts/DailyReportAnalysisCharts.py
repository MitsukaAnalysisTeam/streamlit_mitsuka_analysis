import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import plotly.graph_objects as go

'''
グラフ生成用の関数を定義するファイル
'''
class DailyReportAnalysisCharts:
    '''
    日報分析クラス用の画像生成クラス
    '''
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
        plt.xticks(rotation=-90, fontsize=30)
        plt.yticks(fontsize = 25)
        if "売上" in str1 or "客単価" in str1 :
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            plt.ylabel("月の総売上(円)", fontsize=40)
        elif "客数" in str1:
            plt.ylabel("月の総客数(人)", fontsize=40)
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
        plt.xlabel("年/月(営業日数)", fontsize=40)
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
        plt.xticks(rotation=-90, fontsize=30)
        plt.yticks(fontsize = 25)
        if "売上" in str1 or "客単価" in str1:
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            plt.ylabel("月の総売上(円)", fontsize=40)
        elif "客数" in str1:
            plt.ylabel("月の総客数(人)", fontsize=40)
            plt.gca().yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
        plt.xlabel("年/月(営業日数)", fontsize=40)
        plt.grid(axis='y', zorder=0)
        st.pyplot(fig)


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

        # "売上" や "客単価" の場合は通貨フォーマット
        if "売上" in str1 or "客単価" in str1:
            fig.update_layout(
                yaxis_tickformat="¥",  # 通貨のフォーマット
                yaxis_title="月の総売上(円)",
            )
        # "客数" の場合は人数フォーマット
        elif "客数" in str1:
            fig.update_layout(
                yaxis_title="月の総客数(人)",
            )

        # x軸の設定 (日付ラベル、回転角度、フォントサイズ)
        fig.update_layout(
            xaxis=dict(
                tickvals=np.arange(0, len(df1.index), 1),
                ticktext=df1.index.tolist(),
                tickfont=dict(size=15),
            ),
            yaxis=dict(
                tickfont=dict(size=15),
            ),
            title=f'{date1}と{date2}の{str1}の曜日別比較',
            barmode='group',  # バーをグループ化
            showlegend=True,
            legend=dict(
                title="月",
                font=dict(size=18),
                x=0.01,
                y=0.99
            ),
            xaxis_title="日付",
            margin=dict(l=40, r=40, t=40, b=80),  # ラベルが切れないようにマージンを調整
            plot_bgcolor='white',
        )

        # Streamlit でグラフを表示
        st.plotly_chart(fig, use_container_width=True)