import streamlit as st
import pandas as pd
import os
import numpy as np
import src.components.charts as charts
import src.components.utils as utils


def show():
    daily_report_analysis()

def daily_report_analysis():
    '''
    ある月のグラフ表示
    '''
    # インスタンス化
    dailyReportAnalysisUtils = utils.DailyReportAnalysisUtils()
    dailyReportAnalysisCharts = charts.DailyReportAnalysisCharts()
    st.header("Analytics Page")
    # バーでファイルを選択
    month_list = utils.get_month_list()
    selected_month = st.selectbox("日報ファイルを選択", month_list[::-1])

    file_path = dailyReportAnalysisUtils.get_file_path_by_date(selected_month)
    try:
        # データの読み込み
        data = pd.read_csv(file_path,index_col=0)
        data = dailyReportAnalysisUtils.convert_daily_report_data(data)
        # 客数か売上を選択
        option_daily = st.selectbox("↓↓↓売上か客数を選択↓↓↓", ["売上","客数","客単価"])
        # グラフ表示
        st.write("###日単位の売上・客数データ")
        if option_daily == "売上":
            dailyReportAnalysisCharts.lunch_night_stacked_bar(data, option_daily+'(昼)', option_daily+'(夜)', '売上額 (¥)')
        elif option_daily == "客数":
            dailyReportAnalysisCharts.lunch_night_stacked_bar(data, option_daily+'(昼)', option_daily+'(夜)', '客数 (人)')
        else: # 客単価
            dailyReportAnalysisCharts.daily_price_per_customer_bar(data)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

    '''
    月毎のグラフ表示
    '''
    st.write("###月単位の売上・客数データ")
    df_dic = dailyReportAnalysisUtils.get_all_daily_report_dic()
    option_monthly_sum = st.selectbox("表示させる項目", [s for s in df_dic["2022"]["10"].columns.tolist()[1:] if "客単価" not in s])
    dailyReportAnalysisCharts.monthly_transfer_sum_bar(df_dic=df_dic,
                                                   str1=option_monthly_sum)
    option_monthly_mean = st.selectbox("表示させる項目", df_dic["2022"]["10"].columns.tolist()[1:])
    dailyReportAnalysisCharts.monthly_transfer_mean_bar(df_dic=df_dic,
                                                   str1=option_monthly_mean)
    

