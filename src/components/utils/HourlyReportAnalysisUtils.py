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


class HourlyReportAnalysisUtils:
    """
    時間別分析用のユーティリティクラス
    """
    def __init__(self):
        self.df_cus_dic  = self.get_all_hourly_report_dic(spreadsheet_name="客数_sum")
        self.df_sale_dic = self.get_all_hourly_report_dic(spreadsheet_name="売上_sum")

    # ───────────────────────
    # SpreadSheets からの取得
    # ───────────────────────
    def get_df_from_ss(self, spreadsheet_name: str) -> pd.DataFrame:
        """
        指定したスプレッドシート名から全期間データを取得する。
        DailyReportAnalysisUtils.get_df_from_ss と同じパターン。
        """
        try:
            spreadsheet = SpreadSheets.SpreadSheets()
            ss_id = spreadsheet.get_spreadsheet_id_by_name(
                folder_id="1Kbu-rDXUcROQgkH-_xcsz3ItjxfCWz2y",
                spreadsheet_name=spreadsheet_name
            )
            ss = spreadsheet.get_spreadsheet_by_id(ss_id)
            worksheet = ss.worksheet("シート1")
            df = spreadsheet.get_df_from_worksheet(worksheet)

            if "日付" in df.columns:
                df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
                df = df.dropna(subset=["日付"])
                df = df.set_index("日付")
            df = df.replace(r"^\s*$", np.nan, regex=True)
            return df
        except Exception as e:
            print(f"get_df_from_ss でエラー: {e}")
            return pd.DataFrame()

    # ──────────────
    # 月別辞書の構築
    # ──────────────
    def set_all_hourly_report_dic(self, spreadsheet_name: str) -> dict:
        """
        全期間データを月別に分割して辞書化する。
        構造: { "2024": { "3": DataFrame, "4": DataFrame, ... }, ... }
        """
        month_list = self.get_month_list()
        df = self.get_df_from_ss(spreadsheet_name)
        if df.empty:
            return {}

        df_dic: dict[str, dict[str, pd.DataFrame]] = {}

        for ym in month_list:
            year_str, month_str = ym.split("_")
            y = int(year_str)
            m = int(month_str)

            df_dic.setdefault(year_str, {})
            mask = (df.index.year == y) & (df.index.month == m)
            df_dic[year_str][month_str] = df.loc[mask]

        return df_dic

    def get_all_hourly_report_dic(self, spreadsheet_name: str) -> dict:
        """
        月別辞書を構築し、convert_hourly_report_data を各月に適用する。
        """
        df_dic = self.set_all_hourly_report_dic(spreadsheet_name)

        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    df_dic[year][month] = self.convert_hourly_report_data(df)
                except Exception as e:
                    print(f"エラー: 年={year}, 月={month}, {e}")

        return df_dic

    # pd.DataFrame を時間別分析用の形式に変換するメソッド
    def convert_hourly_report_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.loc[:, ['11時', '12時', '13時', '14時', '15時', '16時',
                        '17時', '18時', '19時', '20時', '21時', '22時', '23時']].dropna()
        df = df.loc[(df != 0).any(axis=1)]
        df.index = pd.to_datetime(df.index)

        time_cols = ['11時', '12時', '13時', '14時', '15時', '16時',
                    '17時', '18時', '19時', '20時', '21時', '22時', '23時']
        df[time_cols] = df[time_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        df["曜日"] = df.index.dayofweek.map(
            {0: '月', 1: '火', 2: '水', 3: '木', 4: '金', 5: '土', 6: '日'}
        )
        df.index = df.index.map(lambda x: x.strftime("%Y-%m-%d"))
        return df

    # 週別の平均を取るためのメソッド
    def get_week_groupby_mean(self, df: pd.DataFrame) -> pd.DataFrame:
        week_group_mean = df.groupby('曜日').mean().round(1)
        week_group_mean = week_group_mean.reindex(index=['水', '木', '金', '土', '日'])
        return week_group_mean

    """
    辞書から指定年月のDataFrameを取得する
    これにより、分析ページでのコードがシンプルになる
    (データ取得してpd.DataFrameに変換する処理をここに集約できるため)
    """
    def get_df_from_dic(self, date: str, kind: str = "客数") -> pd.DataFrame:
        """
        辞書から指定年月のDataFrameを取得する。
        kind: "客数" or "売上"
        """
        year  = date[:4]
        month = date.split('_')[1]
        # 客数or売上の辞書を選択
        df_dic = self.df_cus_dic if kind == "客数" else self.df_sale_dic
        try:
            # 指定した年月のDataFrameを返す
            return df_dic[year][month]
        except Exception as e:
            print(f"get_df_from_dic でエラー: {e}")
            return pd.DataFrame()

    # 2022年10月から現在までの月リスト(["2022_10", "2022_11", ...])を生成するメソッド
    def get_month_list(self) -> list:
        now = datetime.now() - relativedelta(months=1)
        current_year  = now.year
        current_month = now.month

        def generate_month_list(start_year, start_month, end_year, end_month):
            start_date = datetime(start_year, start_month, 1)
            end_date   = datetime(end_year,   end_month,   1)
            month_list = []
            while start_date <= end_date:
                month_list.append(f"{start_date.year}_{start_date.month}")
                start_date += timedelta(days=31)
                start_date  = start_date.replace(day=1)
            return month_list

        return generate_month_list(2022, 10, current_year, current_month)