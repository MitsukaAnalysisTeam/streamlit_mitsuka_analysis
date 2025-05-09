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
        # 指定された曜日が存在しない場合は全ての曜日を表示
        if selected_days is None or selected_days == "全体":
            filtered_df = df_week
        else:
            # 指定された曜日のみをフィルタリング
            filtered_df = df_week.loc[[selected_days]]
        
        # 表示するデータがない場合
        if filtered_df.empty:
            st.warning("選択された曜日のデータがありません。")
            return
            
        # 転置して時間データを取り出し、棒グラフを作成
        fig, ax = plt.subplots(figsize=(15, 5))
        
        # グリッドを背景に設定（棒グラフの描画前に配置）
        ax.grid(True, zorder=0)
        
        # フィルタリングされたデータを使用
        filtered_df.T.iloc[0:len(self.time_dic), :].plot.bar(
            ax=ax,
            width=0.8,
            color=self.color_day_dic,
            edgecolor='black',
            linewidth=1,
            zorder=3  # zorderを高く設定して前面に表示
        )

        # 軸ラベルの設定
        if "売上" in label or "客単価" in label:
            ax.yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
            ax.set_ylabel("月の総売上(円)", fontsize=15)
            ax.set_ylim(0, 35000)  # 売上の上限を¥35,000に設定
        elif "客数" in label:
            ax.set_ylabel("月の総客数(人)", fontsize=15)
            ax.yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
            ax.set_ylim(0, 30)  # 客数の上限を30人に設定

        # 軸のフォントサイズ設定
        ax.tick_params(axis='x', labelsize=15, rotation=0)
        ax.tick_params(axis='y', labelsize=15)

        # グラフのラベルと凡例
        ax.set_ylabel(label)
        ax.legend(fontsize=9, loc='upper right')
        
        # グリッドを確実に表示（念のため再設定）
        plt.grid(True)
        
        # グラフをStreamlitで表示
        st.pyplot(fig)

    def compare_two_data(self, df1, df2, label, title1, title2, selected_days1=None, selected_days2=None):
        """
        2つのデータを横に並べて比較するグラフを作成
        
        Parameters:
        -----------
        df1 : DataFrame
            比較する1つ目のデータ
        df2 : DataFrame
            比較する2つ目のデータ
        label : str
            グラフのラベル
        title1 : str
            1つ目のデータのタイトル
        title2 : str
            2つ目のデータのタイトル
        selected_days1 : str or list, optional
            1つ目のデータで表示する曜日。Noneの場合は全ての曜日を表示
        selected_days2 : str or list, optional
            2つ目のデータで表示する曜日。Noneの場合は全ての曜日を表示
        """
        # 2列のレイアウトを作成
        cols = st.columns(2)
        
        # 1つ目のデータ
        with cols[0]:
            st.write(f"**{title1}**")
            if df1 is not None and not df1.empty:
                # フィルタリング
                if selected_days1 is None or selected_days1 == "全体":
                    filtered_df1 = df1
                else:
                    try:
                        filtered_df1 = df1.loc[[selected_days1]] if isinstance(selected_days1, str) else df1.loc[selected_days1]
                    except KeyError:
                        st.warning(f"選択された曜日 '{selected_days1}' のデータがありません。")
                        return
                
                if not filtered_df1.empty:
                    # グラフ作成
                    fig1, ax1 = plt.subplots(figsize=(8, 5))
                    ax1.grid(True, zorder=0)
                    
                    filtered_df1.T.iloc[0:len(self.time_dic), :].plot.bar(
                        ax=ax1,
                        width=0.8,
                        color=self.color_day_dic,
                        edgecolor='black',
                        linewidth=1,
                        zorder=3
                    )
                    
                    # 軸ラベルの設定
                    if "売上" in label or "客単価" in label:
                        ax1.yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
                        ax1.set_ylabel("月の総売上(円)", fontsize=10)
                        ax1.set_ylim(0, 35000)
                    elif "客数" in label:
                        ax1.set_ylabel("月の総客数(人)", fontsize=10)
                        ax1.yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
                        ax1.set_ylim(0, 30)
                    
                    ax1.tick_params(axis='x', labelsize=10, rotation=0)
                    ax1.tick_params(axis='y', labelsize=10)
                    ax1.set_ylabel(label, fontsize=10)
                    ax1.legend(fontsize=8, loc='upper right')
                    plt.grid(True)
                    st.pyplot(fig1)
                else:
                    st.warning("表示するデータがありません。")
            else:
                st.warning("データが存在しません。")
        
        # 2つ目のデータ
        with cols[1]:
            st.write(f"**{title2}**")
            if df2 is not None and not df2.empty:
                # フィルタリング
                if selected_days2 is None or selected_days2 == "全体":
                    filtered_df2 = df2
                else:
                    try:
                        filtered_df2 = df2.loc[[selected_days2]] if isinstance(selected_days2, str) else df2.loc[selected_days2]
                    except KeyError:
                        st.warning(f"選択された曜日 '{selected_days2}' のデータがありません。")
                        return
                
                if not filtered_df2.empty:
                    # グラフ作成
                    fig2, ax2 = plt.subplots(figsize=(8, 5))
                    ax2.grid(True, zorder=0)
                    
                    filtered_df2.T.iloc[0:len(self.time_dic), :].plot.bar(
                        ax=ax2,
                        width=0.8,
                        color=self.color_day_dic,
                        edgecolor='black',
                        linewidth=1,
                        zorder=3
                    )
                    
                    # 軸ラベルの設定
                    if "売上" in label or "客単価" in label:
                        ax2.yaxis.set_major_formatter(FuncFormatter(self.currency_formatter))
                        ax2.set_ylabel("月の総売上(円)", fontsize=10)
                        ax2.set_ylim(0, 35000)
                    elif "客数" in label:
                        ax2.set_ylabel("月の総客数(人)", fontsize=10)
                        ax2.yaxis.set_major_formatter(FuncFormatter(self.customer_formatter))
                        ax2.set_ylim(0, 30)
                    
                    ax2.tick_params(axis='x', labelsize=10, rotation=0)
                    ax2.tick_params(axis='y', labelsize=10)
                    ax2.set_ylabel(label, fontsize=10)
                    ax2.legend(fontsize=8, loc='upper right')
                    plt.grid(True)
                    st.pyplot(fig2)
                else:
                    st.warning("表示するデータがありません。")
            else:
                st.warning("データが存在しません。")

