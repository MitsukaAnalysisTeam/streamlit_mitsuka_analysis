from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import japanize_matplotlib
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import src.components.utils.common.SpreadSheets as SpreadSheets
from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap
japanize_matplotlib.japanize()

class LunchAnalysisUtils:
    def __init__(self, category_unify_map: CategoryUnifyMap = None):
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

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
        ramen_series_list = []
        for key, df in df_dict.items():
            if not self._category_unify_map.is_ramen(key):
                continue
            series_sum = df.sum(axis=1).rename(key)
            ramen_series_list.append(series_sum)

        # データが一つもなかった場合は、空のDataFrameを返す
        if not ramen_series_list:
            return pd.DataFrame()

        # リストに格納したすべてのSeriesを一度に連結する
        ramen_df = pd.concat(ramen_series_list, axis=1)

        # NaN（対象の日に売上がなかった商品など）を0で埋める
        ramen_df = ramen_df.fillna(0)

        return ramen_df