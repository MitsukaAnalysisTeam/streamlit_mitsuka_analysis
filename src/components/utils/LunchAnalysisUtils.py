from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import japanize_matplotlib
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import src.components.utils.SpreadSheets as SpreadSheets
japanize_matplotlib.japanize()

class LunchAnalysisUtils:
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
        return month_list
    
    def prepare_ramen_df_num(self, df_dict: dict) -> pd.DataFrame:
        """
        カテゴリ別に集計済みのDataFrame辞書から、日々の売上合計を算出して
        一つのDataFrameにまとめる関数。
        """
        ramen_keys = self.__get_ramen_list()
        
        ramen_series_list = []
        for key in ramen_keys:
            if key in df_dict:
                series_sum = df_dict[key].sum(axis=1).rename(key)
                ramen_series_list.append(series_sum)
            else:
                # データがないカテゴリについては警告を出す（任意）
                print(f"Warning: Category '{key}' not found in df_dict")

        # データが一つもなかった場合は、空のDataFrameを返す
        if not ramen_series_list:
            return pd.DataFrame()

        # リストに格納したすべてのSeriesを一度に連結する
        ramen_df = pd.concat(ramen_series_list, axis=1)
        
        # NaN（対象の日に売上がなかった商品など）を0で埋める
        ramen_df = ramen_df.fillna(0)

        return ramen_df

    
    def __get_ramen_list(self):
        ramen_list = [
            "カリー",
            "カリーつけ麺",
            "海老みそ",
            "焦がし海老味噌",
            "ベジ味噌",
            "白味噌",
        ]
        return ramen_list