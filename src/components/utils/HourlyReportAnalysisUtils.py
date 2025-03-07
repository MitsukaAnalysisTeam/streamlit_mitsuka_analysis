from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import jpholiday
import japanize_matplotlib
import os
import re 
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

import json
 
japanize_matplotlib.japanize()

    
class HourlyReportAnalysisUtils:
    '''
    時間別データ用のメソッド追加クラス
    '''
    def convert_hourly_report_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # 必要なカラムだけを抽出し、全ての値が0の行を削除
        df = df.loc[:, ['11時', '12時', '13時', '14時', '15時', '16時', '17時', '18時', '19時', '20時', '21時', '22時', '23時']].dropna()
        df = df.loc[(df != 0).any(axis=1)]
        # インデックスを datetime 型に変換（保持）
        df.index = pd.to_datetime(df.index)

        # インデックスから曜日を取得し、"曜日" カラムとして追加
        df["曜日"] = df.index.dayofweek.map({0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'})
        
        # 表示の際にインデックスをフォーマット
        df.index = df.index.map(lambda x: x.strftime("%Y-%m-%d"))
        return df

    
    def get_cus_file_path_by_date(
            self,
            date: str
            )-> str: 
        # データフォルダのパス
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/processed/hourly_report/customer_num"))
        
        # ディレクトリ内のCSVファイルをリストアップ
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        matched_file = [s for s in csv_files if re.match(f'.*{date}.*', s)]

        # ファイルが見つかった場合はフルパスを返す
        if matched_file:
            return os.path.join(data_dir, matched_file[0])
        
        # 見つからない場合は空文字列を返す
        return ""
    
    def get_sales_file_path_by_date(
            self,
            date: str
            )-> str: 
        # データフォルダのパス
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/processed/hourly_report/sales_sum"))
        
        # ディレクトリ内のCSVファイルをリストアップ
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        matched_file = [s for s in csv_files if re.match(f'.*{date}.*', s)]

        # ファイルが見つかった場合はフルパスを返す
        if matched_file:
            return os.path.join(data_dir, matched_file[0])
        
        # 見つからない場合は空文字列を返す
        return ""
    
    def get_week_groupby_mean(
            self,
            df: pd.DataFrame
            )->pd.DataFrame:
        week_group_mean = df.groupby('曜日').mean().round(1)
        week_group_mean = week_group_mean.reindex(index=['水', '木', '金','土','日'])
        return week_group_mean
    
    def get_month_list():
        now = datetime.now() - relativedelta(months=1)
        current_year = now.year
        current_month = now.month

        def generate_month_list(start_year, start_month, end_year, end_month):
            start_date = datetime(start_year, start_month, 1)
            end_date = datetime(end_year, end_month, 1)
            month_list = []

            while start_date <= end_date:
                # 月の部分に先頭のゼロを付けないフォーマットを使用
                month_list.append(f"{start_date.year}_{start_date.month}")
                start_date += timedelta(days=31)
                start_date = start_date.replace(day=1)

            return month_list

        month_list = generate_month_list(2022, 10, current_year, current_month)
        # print(month_list)
        return month_list       