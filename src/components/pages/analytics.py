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
from src.components.utils.MidnightAnalysisUtils import MidnightAnalysisUtils
from src.components.utils.DinerAnalysisUtils import DinerAnalysisUtils
from src.components.charts.RamenAnalysisCharts import RamenAnalysisCharts
from src.components.utils.AlcoholAnalysisUtils import AlcoholAnalysisUtils
from src.components.charts.AlcoholAnalysisCharts import AlcoholAnalysisCharts
from src.components.utils.GetByProductDf import GetByProductDf
from src.components.utils.Json import read_json_file

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

@st.cache_resource
def get_midnight_analysis_utils() -> MidnightAnalysisUtils:
    return MidnightAnalysisUtils()

@st.cache_resource
def get_diner_analysis_utils() -> DinerAnalysisUtils:
    return DinerAnalysisUtils()

@st.cache_resource
def get_ramen_analysis_charts() -> RamenAnalysisCharts:
    return RamenAnalysisCharts()

"""
@st.cache_resource
def get_midnight_analysis_charts() -> MidnightAnalysisCharts:
    return MidnightAnalysisCharts()
"""

@st.cache_resource
def get_alcohol_analysis_utils() -> AlcoholAnalysisUtils:
    return AlcoholAnalysisUtils()

@st.cache_resource
def get_alcohol_analysis_charts() -> AlcoholAnalysisCharts:
    return AlcoholAnalysisCharts()

@st.cache_resource
def get_by_product_df() -> GetByProductDf:
    return GetByProductDf()

# ここでキャッシュされたインスタンスをグローバル変数に格納（実際の関数内でも取得可能）
dailyReportAnalysisUtils = get_daily_report_analysis_utils()
dailyReportAnalysisCharts = get_daily_report_analysis_charts()
hourlyReportAnalysisUtils = get_hourly_report_analysis_utils()
hourlyReportAnalysisCharts = get_hourly_report_analysis_charts()
lunchAnalysisUtils = get_lunch_analysis_utils()
lunchAnalysisCharts = get_lunch_analysis_charts()
midnightAnalysisUtils = get_midnight_analysis_utils()
dinerAnalysisUtils = get_diner_analysis_utils()
ramenAnalysisCharts = get_ramen_analysis_charts()

#MidnightAnalysisCharts = get_midnight_analysis_charts()
alcoholAnalysisUtils = get_alcohol_analysis_utils()
alcoholAnalysisCharts = get_alcohol_analysis_charts()
getByProductDf = get_by_product_df()


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
    month_list = hourlyReportAnalysisUtils.get_month_list()
    selected_month = st.selectbox("表示したい年月を選択", month_list[::-1])
    try:
        option_daily = st.selectbox("↓↓↓売上か客数を選択↓↓↓", ["客数","売上"])
        # 曜日選択をマルチセレクトボックスに変更
        days = ["水", "木", "金", "土", "日"]
        day_options = ["全体"] + days
        selected_days = st.selectbox("表示したい曜日を選択", day_options)
        
        
        # グラフ表示
        st.write(f'{selected_month}の時間別の{option_daily}データ({selected_days})')

        # メインデータ取得・表示
        kind  = "売上" if option_daily == "売上" else "客数"
        label = '売上額 (¥)' if option_daily == "売上" else '客数 (人)'

        #売上or客数のデータを取得し、pd.DataFrameに変換
        data = hourlyReportAnalysisUtils.get_df_from_dic(selected_month, kind=kind)
        if data.empty:
            st.warning("該当月のデータがありません")
            return 

        data = hourlyReportAnalysisUtils.get_week_groupby_mean(data)
        # 曜日を渡すように修正
        hourlyReportAnalysisCharts.week_comp_bar(data, label, selected_days)

            
        # 比較分析セクション
        st.markdown("---")
        st.subheader("データ比較")
        
        # 比較する対象（売上/客数）を選択
        compare_option = st.selectbox("比較する対象", ["売上", "客数"], key="compare_option")
        compare_label  = '売上額 (¥)' if compare_option == "売上" else '客数 (人)'
        compare_kind   = "売上" if compare_option == "売上" else "客数"
        
        # 2つのデータを比較するためのUI
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**1つ目のデータ**")
            first_month = st.selectbox("月を選択", month_list[::-1], key="first_month")
            first_day = st.selectbox("曜日を選択", day_options, key="first_day_month")
        
        with col2:
            st.write("**2つ目のデータ**")
            second_month = st.selectbox("月を選択", month_list[::-1], key="second_month")
            second_day = st.selectbox("曜日を選択", day_options, key="second_day_month")
        
        # 比較データ取得、kindで売上か客数かを選択し、pd.DataFrameに変換
        first_data  = hourlyReportAnalysisUtils.get_df_from_dic(first_month,  kind=compare_kind)
        second_data = hourlyReportAnalysisUtils.get_df_from_dic(second_month, kind=compare_kind)

        if first_data.empty:
            st.warning(f"{first_month}のデータが見つかりません。")
            return
        if second_data.empty:
            st.warning(f"{second_month}のデータが見つかりません。")
            return
        
        # 曜日を渡すように修正
        first_data  = hourlyReportAnalysisUtils.get_week_groupby_mean(first_data)
        second_data = hourlyReportAnalysisUtils.get_week_groupby_mean(second_data)
            
        # 比較グラフの表示
        hourlyReportAnalysisCharts.compare_two_data(
            first_data, second_data,
            compare_label,
            f"{first_month} ({first_day})",
            f"{second_month} ({second_day})",
            first_day  if first_day  != "全体" else None,
            second_day if second_day != "全体" else None
        )
            
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


def ramen_analysis():
    '''
    ラーメン分析のグラフ
    '''
    try:
        # ラーメンの種類を選択
        option_time = st.selectbox("時間帯", ["昼","夜","深夜","全体"])

        # 月リストを新しい順で取得
        month_list = lunchAnalysisUtils.get_month_list()[::-1]

        col1, col2 = st.columns(2)
        with col1:
            option_month_start = st.selectbox("開始月", month_list, index=0)
        with col2:
            # 終了月の初期値を開始月と同じにする
            start_idx = month_list.index(option_month_start)
            option_month_end = st.selectbox("終了月", month_list, index=start_idx)

        # 開始 > 終了の逆転を防ぐ（古い順のインデックスで比較）
        month_list_asc = lunchAnalysisUtils.get_month_list()  # 昇順
        idx_start = month_list_asc.index(option_month_start)
        idx_end   = month_list_asc.index(option_month_end)
        if idx_start > idx_end:
            st.warning("⚠️ 開始月が終了月より新しいです。開始月と終了月を入れ替えて表示します。")
            option_month_start, option_month_end = option_month_end, option_month_start


        df_val_num = getByProductDf.df_all_num

        lunch_json = read_json_file(filepath='data/json/lunch.json')
        midnight_json = read_json_file(filepath='data/json/深夜限定.json')
        diner_json = read_json_file(filepath='data/json/ディナー.json')

        df_val_num_lunch_dict = getByProductDf.json_to_df_dict(df_all=df_val_num
                                                 ,json_dict=lunch_json)
        df_val_num_midnight_dict = getByProductDf.json_to_df_dict(df_all=df_val_num
                                                   ,json_dict=midnight_json)
        df_val_num_diner_dict = getByProductDf.json_to_df_dict(df_all=df_val_num
                                                  ,json_dict=diner_json)

        df_lunch = lunchAnalysisUtils.prepare_ramen_df_num(df_val_num_lunch_dict)
        df_midnight = midnightAnalysisUtils.prepare_midnight_df_num(df_val_num_midnight_dict)
        df_diner = dinerAnalysisUtils.prepare_diner_df_num(df_val_num_diner_dict)

        charts = RamenAnalysisCharts()

        st.subheader("🥣 ラーメン提供割合（円グラフ）")
        charts.pie_ramen_ratio_by_time(
            df_lunch, df_diner, df_midnight,
            time_filter=option_time,
            month_start=option_month_start,
            month_end=option_month_end,
        )

        st.subheader("📊 曜日別ラーメン提供杯数（棒グラフ）")
        charts.bar_ramen_by_weekday(
            df_lunch, df_diner, df_midnight,
            time_filter=option_time,
            month_start=option_month_start,
            month_end=option_month_end,
        )


    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

def lunch_ramen_analysis():
    month_list = lunchAnalysisUtils.get_month_list()
    selected_month = st.selectbox("どの年月を表示しますか？", month_list[::-1])

    df_val_num  = getByProductDf.df_all_num
    lunch_json  = read_json_file(filepath='data/json/lunch.json')
    df_val_num_dict = getByProductDf.json_to_df_dict(
        df_all=df_val_num, json_dict=lunch_json
    )
    df_ramen = lunchAnalysisUtils.prepare_ramen_df_num(df_val_num_dict)
    result_ramen = lunchAnalysisUtils.summarize_ramen_sales(df_ramen, selected_month)

    # 追加グラフ
    st.subheader("🥣 昼カテゴリ別提供数")
    lunchAnalysisCharts.pie_lunch_category(df_val_num_dict, selected_month)

    st.subheader("🍱 セットメニュー内訳")
    lunchAnalysisCharts.pie_set_menu(df_val_num_dict, selected_month)


def alchohol_analysis():
    '''
    アルコール分析のグラフ
    '''
    try:
        # アルコールの種類を選択
        option_alcohol = st.selectbox("アルコールの種類", ["アルコール合計","ビール","秋鹿","若尾ワイン"])
        option_daily = st.selectbox("平均杯数・合計売上", ["平均杯数","合計売上"])
        # グラフ表示
        st.write(f'月単位の{option_alcohol}データ')


        df_val_num = getByProductDf.df_all_num
        df_val_sale = getByProductDf.df_all_sale

        alcohol_json = read_json_file(filepath='data/json/alcohol.json')
        df_val_num_dict = getByProductDf.json_to_df_dict(df_all=df_val_num
                                                    ,json_dict=alcohol_json)
        df_val_sale_dict = getByProductDf.json_to_df_dict(df_all=df_val_sale
                                                    ,json_dict=alcohol_json)
        
        df_alcohol_num = alcoholAnalysisUtils.prepare_alcohol_df_num(df_val_num_dict)
        df_alcohol_num = df_alcohol_num.reset_index()
        df_alcohol_sale = alcoholAnalysisUtils.prepare_alcohol_df_num(df_val_sale_dict)
        df_alcohol_sale = df_alcohol_sale.reset_index()
        
        if option_alcohol == "アルコール合計":
            if option_daily == "平均杯数":
                data = alcoholAnalysisUtils.get_alchol_data(df_alcohol_num)
                alcoholAnalysisCharts.alchol_graph(data)
            else: #
                data = alcoholAnalysisUtils.get_alchol_data(df_alcohol_sale)
                alcoholAnalysisCharts.alchol_graph(data)
        elif option_alcohol == "ビール":
            if option_daily == "平均杯数":
                data = alcoholAnalysisUtils.get_beer_data(df_alcohol_num)
                alcoholAnalysisCharts.beer_graph(data)
            else:
                data = alcoholAnalysisUtils.get_beer_data(df_alcohol_sale)
                alcoholAnalysisCharts.beer_graph(data)
        elif option_alcohol == "秋鹿":
            if option_daily == "平均杯数":
                #データの読み込み
                data = alcoholAnalysisUtils.get_akishika_data(df_alcohol_num)
                alcoholAnalysisCharts.akishika_graph(data)
            else:
                # データの読み込み
                data = alcoholAnalysisUtils.get_akishika_data(df_alcohol_sale)
                alcoholAnalysisCharts.akishika_graph(data)
        else: # 若尾ワイン
            if option_daily == "平均杯数":
                # データの読み込み
                data = alcoholAnalysisUtils.get_wine_data(df_alcohol_num)
                alcoholAnalysisCharts.wine_graph(data)
            else:
                # データの読み込み
                data = alcoholAnalysisUtils.get_wine_data(df_alcohol_sale)
                alcoholAnalysisCharts.wine_graph(data)
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")