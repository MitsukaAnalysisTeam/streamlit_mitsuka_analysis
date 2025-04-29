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
import src.components.utils.SpreadSheets as SpreadSheets
japanize_matplotlib.japanize()

# Drive 1PDYD1wvqKwsW42Q09VF8JkdldUop0r4R
#  SS 1qCbwxMXHyG3ZcqLqTlxi-MyKffIYiDoTT04KMSQhvSI
class LunchAnalysisUtils:
    def __init__(self):
        self.df_ramen = self.get_lunch_file_ramen()
        self.df_all = self.get_lunch_file_all()

    def get_lunch_file_ramen(
            self
            ) -> pd.DataFrame: 
        return self.get_df_from_ss("ラーメン")
    
    def get_lunch_file_all(
            self
            ) -> pd.DataFrame: 
        return self.get_df_from_ss("df_num_all")
    

    def get_df_from_ss(self,
                       sheet_name:str
                       ) -> pd.DataFrame:
        try:
            spreadsheet = SpreadSheets.SpreadSheets()
            ss_id = spreadsheet.get_spreadsheet_id_by_name(
                folder_id="1PDYD1wvqKwsW42Q09VF8JkdldUop0r4R",
                spreadsheet_name="ランチ分析"
            )
            ss = spreadsheet.get_spreadsheet_by_id(ss_id)
            worksheet = ss.worksheet(sheet_name)
            df = spreadsheet.get_df_from_worksheet(worksheet)

            if "日付" in df.columns:
                # フォーマット指定を外して自動判別に任せる
                df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
                df = df.dropna(subset=["日付"])   # 変換失敗行を除去
                df = df.set_index("日付")
            df = df.replace(r"^\s*$", np.nan, regex=True)
            # print(df)
            return df
        except Exception as e:
            print(f"get_df_from_ss でエラー: {e}")
            return pd.DataFrame()
        

    def summarize_ramen_sales(self, df: pd.DataFrame, date: str) -> pd.Series:
        """
        指定した年と月の各商品の合計販売数を表示する関数
        """
        year = int(date[:4])
        month = int(date.split('_')[1])

        if not pd.api.types.is_datetime64_any_dtype(df.index):
            df.index = pd.to_datetime(df.index)
        target_df = df[(df.index.year == year) & (df.index.month == month)]
        target_df = target_df.apply(pd.to_numeric, errors='coerce')
        filtered_df = target_df.dropna(axis=1, how='all')
        numeric_df = filtered_df.select_dtypes(include=["number"])
        if numeric_df.empty:
            print(f"No numeric data found for {year}-{month}")
        
        summary = numeric_df.sum()
        
        return summary

        
    def get_month_list(self):
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