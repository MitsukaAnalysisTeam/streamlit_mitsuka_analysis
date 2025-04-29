import streamlit as st
import pandas as pd
import os
import numpy as np
import sys
# プロジェクトのルートディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.components.charts.DailyReportAnalysisCharts import DailyReportAnalysisCharts
from src.components.charts.HourlyReportAnalysisCharts import HourlyReportAnalysisCharts
from src.components.utils.DailyReportAnalysisUtils import DailyReportAnalysisUtils
from src.components.utils.HourlyReportAnalysisUtils import HourlyReportAnalysisUtils
from src.components.utils.LunchAnalysisUtils import LunchAnalysisUtils
from src.components.charts.LunchAnalysisCharts import LunchAnalysisCharts

"""
インスタンス化は一回だけにする
キャッシュを保存することで複数回インスタンス化することを防ぐ
"""
@st.cache_resource
def get_daily_report_analysis_utils() -> DailyReportAnalysisUtils:
    return DailyReportAnalysisUtils()

@st.cache_resource
def get_daily_report_analysis_charts() -> DailyReportAnalysisCharts:
    return DailyReportAnalysisCharts()

@st.cache_resource
def get_hourly_report_analysis_utils() -> HourlyReportAnalysisUtils:
    return HourlyReportAnalysisUtils()

@st.cache_resource
def get_hourly_report_analysis_charts() -> HourlyReportAnalysisCharts:
    return HourlyReportAnalysisCharts()

@st.cache_resource
def get_lunch_analysis_utils() -> LunchAnalysisUtils:
    return LunchAnalysisUtils()

@st.cache_resource
def get_lunch_analysis_charts() -> LunchAnalysisCharts:
    return LunchAnalysisCharts()

# ここでキャッシュされたインスタンスをグローバル変数に格納（実際の関数内でも取得可能）
dailyReportAnalysisUtils = get_daily_report_analysis_utils()
dailyReportAnalysisCharts = get_daily_report_analysis_charts()
hourlyReportAnalysisUtils = get_hourly_report_analysis_utils()
hourlyReportAnalysisCharts = get_hourly_report_analysis_charts()
lunchAnalysisUtils = get_lunch_analysis_utils()
lunchAnalysisCharts = get_lunch_analysis_charts()


def show():
    daily_report_analysis()
    monthly_report_analysis()
    weekly_report_analysis()

def daily_report_analysis():
    '''
    ある月のグラフ表示
    '''
    # バーでファイルを選択
    month_list = dailyReportAnalysisUtils.get_month_list()
    selected_month = st.selectbox("日報ファイルを選択", month_list[::-1])

    try:
        # データの読み込み
        data = dailyReportAnalysisUtils.get_df_from_dic(selected_month)
        # 客数か売上を選択
        option_daily = st.selectbox("↓↓↓売上か客数か客単価を選択↓↓↓", ["売上","客数","客単価"])
        # グラフ表示
        st.write(f'{selected_month}の日単位の{option_daily}データ')
        if option_daily == "売上":
            dailyReportAnalysisCharts.lunch_night_stacked_bar(data, option_daily+'(昼)', option_daily+'(夜)', '売上額 (¥)')
        elif option_daily == "客数":
            dailyReportAnalysisCharts.lunch_night_stacked_bar(data, option_daily+'(昼)', option_daily+'(夜)', '客数 (人)')
        else: # 客単価
            dailyReportAnalysisCharts.daily_price_per_customer_bar(data)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")


def hourly_report_analysis():
    '''
    時間別分析のグラフ
    '''
    # バーでファイルを選択
    month_list = HourlyReportAnalysisUtils.get_month_list()
    selected_month = st.selectbox("表示したい年月を選択", month_list[::-1])
    try:
        option_daily = st.selectbox("↓↓↓売上か客数を選択↓↓↓", ["客数","売上"])
        # グラフ表示
        st.write(f'{selected_month}の時間別の{option_daily}データ')
        if option_daily == "売上":
            file_path = hourlyReportAnalysisUtils.get_sales_file_path_by_date(selected_month)
            data = pd.read_csv(file_path,index_col=0)
            data = hourlyReportAnalysisUtils.convert_hourly_report_data(data)
            data = hourlyReportAnalysisUtils.get_week_groupby_mean(data)
            
            hourlyReportAnalysisCharts.week_comp_bar(data, '売上額 (¥)')
        elif option_daily == "客数":
            file_path = hourlyReportAnalysisUtils.get_cus_file_path_by_date(selected_month)
            data = pd.read_csv(file_path,index_col=0)
            data = hourlyReportAnalysisUtils.convert_hourly_report_data(data)
            data = hourlyReportAnalysisUtils.get_week_groupby_mean(data)

            hourlyReportAnalysisCharts.week_comp_bar(data, '客数 (人)')
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")


    
def monthly_report_analysis():
    # インスタンス化
    # dailyReportAnalysisUtils = DailyReportAnalysisUtils()
    # dailyReportAnalysisCharts = DailyReportAnalysisCharts()
    '''
    月毎のグラフ表示
    '''
    st.write("### 月単位の総売上・総客数データ")
    df_dic = dailyReportAnalysisUtils.df_dic
    option_monthly_sum = st.selectbox("表示させる項目", [s for s in df_dic["2022"]["10"].columns.tolist()[1:] if "客単価" not in s])
    dailyReportAnalysisCharts.monthly_transfer_sum_bar(df_dic=df_dic,
                                                   str1=option_monthly_sum)
    st.write("### 月単位の平均売上・平均客数・客単価データ")
    option_monthly_mean = st.selectbox("表示させる項目", df_dic["2022"]["10"].columns.tolist()[1:])
    dailyReportAnalysisCharts.monthly_transfer_mean_bar(df_dic=df_dic,
                                                   str1=option_monthly_mean)
    
def weekly_report_analysis():
    '''
    曜日別のグラフ表示と増減割合表示
    '''
    month_list = dailyReportAnalysisUtils.get_month_list()
    df_dic = dailyReportAnalysisUtils.df_dic
    
    # ユーザーによる年月選択
    left_selected_month_for_weekly = st.selectbox("グラフの左側にくる年月", month_list[:-1][::-1])
    right_selected_month_for_weekly = st.selectbox("グラフの右側にくる年月", month_list[::-1])
    
    # 比較する指標の選択
    option_weekly_mean = st.selectbox("表示", df_dic["2022"]["10"].columns.tolist()[1::])
    
    # 週別データの取得
    df_weekly_dic = dailyReportAnalysisUtils.get_all_weekly_report_dic()
    
    # 左側と右側のデータ取得
    df_left = df_weekly_dic[left_selected_month_for_weekly[:4]][left_selected_month_for_weekly[5:]]
    df_right = df_weekly_dic[right_selected_month_for_weekly[:4]][right_selected_month_for_weekly[5:]]
    
    # 差分計算
    diff_result = dailyReportAnalysisUtils.weekly_get_left_and_right_diff(df_left, df_right, option_weekly_mean)
    
    dailyReportAnalysisCharts.weekly_comparison_bar(
        df_weekly_dic[left_selected_month_for_weekly[:4]][left_selected_month_for_weekly[5:]],
        df_weekly_dic[right_selected_month_for_weekly[:4]][right_selected_month_for_weekly[5:]],
        option_weekly_mean,
        left_selected_month_for_weekly,
        right_selected_month_for_weekly
    )

    st.subheader(f'{right_selected_month_for_weekly[:4]}年{right_selected_month_for_weekly[5:]}月の{option_weekly_mean}({left_selected_month_for_weekly[:4]}年{left_selected_month_for_weekly[5:]}月との変化割合)')
    # 曜日ごとの増減表示
    columns_top = st.columns(3)  # 上段のカラム
    columns_bottom = st.columns(3)  # 下段のカラム

    # 曜日ごとの増減表示（上段: 水、木、金）
    for idx, day in enumerate(['水', '木', '金']):
        right_value = df_right.loc[day, option_weekly_mean]
        change = diff_result.get(day, "N/A")
        
        # 金額を整数として表示し、カンマ区切り
        right_value_int = int(right_value) if isinstance(right_value, (int, float)) else 0
        formatted_value = f"{right_value_int:,.0f}"  # カンマ区切り

        # 増減の表示
        with columns_top[idx]:
            st.metric(day, formatted_value, change)
    
    # 曜日ごとの増減表示（下段: 土、日、祝日）
    for idx, day in enumerate(['土', '日', '祝日']):
        right_value = df_right.loc[day, option_weekly_mean]
        change = diff_result.get(day, "N/A")
        
        # 金額を整数として表示し、カンマ区切り
        right_value_int = int(right_value) if isinstance(right_value, (int, float)) else 0
        formatted_value = f"{right_value_int:,.0f}"  # カンマ区切り

        # 増減の表示
        with columns_bottom[idx]:
            st.metric(day, formatted_value, change)


def night_ramen_analysis():
    '''
    夜ラーメン分析のグラフ
    '''
    st.title("開発中...🐭")

def lunch_ramen_analysis():
    '''
    ランチラーメン分析のグラフ
    '''
    st.title("開発中...🐭")
    month_list = lunchAnalysisUtils.get_month_list()
    selected_month = st.selectbox("どの年月を表示しますか？", month_list[::-1])

    df_ramen = lunchAnalysisUtils.df_ramen
    df_all = lunchAnalysisUtils.df_all

    result_ramen = lunchAnalysisUtils.summarize_ramen_sales(df_ramen, selected_month)
    lunchAnalysisCharts.bar_ranking_df(result_ramen, selected_month, "ラーメンの合計販売数")

    result_all = lunchAnalysisUtils.summarize_ramen_sales(df_all, selected_month)
    lunchAnalysisCharts.bar_ranking_df(result_all, selected_month, "ランチ全商品の合計販売数")

def alchohol_analysis():
    '''
    アルコール分析のグラフ
    '''
    st.title("開発中...🐭")