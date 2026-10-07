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

class DinerAnalysisUtils:
    def __init__(self, category_unify_map: CategoryUnifyMap = None):
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def prepare_diner_df_num(self, df_dict: dict) -> pd.DataFrame:
        """
        カテゴリ別に集計済みのDataFrame辞書から、日々の売上合計を算出して
        一つのDataFrameにまとめる関数。
        """
        diner_series_list = []
        for key, df in df_dict.items():
            if not self._category_unify_map.is_ramen(key):
                continue
            series_sum = df.sum(axis=1).rename(key)
            diner_series_list.append(series_sum)

        # データが一つもなかった場合は、空のDataFrameを返す
        if not diner_series_list:
            return pd.DataFrame()

        # リストに格納したすべてのSeriesを一度に連結する
        diner_df = pd.concat(diner_series_list, axis=1)

        # NaN（対象の日に売上がなかった商品など）を0で埋める
        diner_df = diner_df.fillna(0)

        return diner_df