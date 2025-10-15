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

'''
データの処理を行うファイル。
'''
class DailyReportAnalysisUtils:
    def __init__(self) -> None:
        self.df_dic = self.get_all_daily_report_dic()

    '''
    日報データ用のメソッド追加クラス
    '''
    def convert_daily_report_data(
            self,
            df: pd.DataFrame
            ) -> pd.DataFrame:
        # df = df[df['曜日'].isin(['月','火','水','木','金','土','日'])]
        df = df.loc[:,['曜日','売上(昼)','客数(昼)','客単価(昼)','売上(夜)','客数(夜)','客単価(夜)','1日総売上','1日総客数','1日客単価']].dropna()
        for col in ['客数(夜)', '売上(夜)', '客単価(夜)', '客数(昼)', '売上(昼)', '客単価(昼)', '1日総客数', '1日総売上', '1日客単価']:
            df[col] = (
                df[col].astype(str)
                .str.replace('人', '', regex=True)
                .str.replace('¥', '', regex=True)
                .str.replace(',', '', regex=True)
                .str.replace('#DIV/0!','0', regex=True)
            )
        df['客単価(夜)'] = df['客単価(夜)'].replace('#DIV/0!', '0')
        df['客数(夜)'] = df['客数(夜)'].astype(int)
        df['売上(夜)'] = df['売上(夜)'].astype(int)
        df['客単価(夜)'] = df['客単価(夜)'].astype(float)
        df['客数(昼)'] = df['客数(昼)'].astype(int)
        df['売上(昼)'] = df['売上(昼)'].astype(int)
        df['客単価(昼)'] = df['客単価(昼)'].astype(float)
        df['1日総客数'] = df['1日総客数'].astype(int)
        df['1日総売上'] = df['1日総売上'].astype(int)
        df['1日客単価'] = df['1日客単価'].astype(float)

        df = self.__add_df_jpholiday(df)
        df = self.__df_reindex_date(df)
        return df

    def __add_df_jpholiday(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        index（DatetimeIndex）を直接使って祝日判定し、
        曜日列を書き換えます。
        """
        # DatetimeIndex のままループ
        for i, dt in enumerate(df.index):
            # dt は pandas.Timestamp
            if jpholiday.is_holiday(dt.date()):
                df.iat[i, 0] = '祝日'   # 1列目（曜日）を書き換え
        return df
    
    def __df_reindex_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        インデックスを「月/日(曜日)」の文字列に置き換え。
        """
        new_index = [
            f"{ts.month}/{ts.day}({df.iloc[i,0]})"
            for i, ts in enumerate(df.index)
        ]
        df = df.copy()
        df.index = new_index
        return df

    

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
    
    """
    日報データをスプレッドシートから取得する手順
    1. SpreadSheet クラスを用いて、スプレッドシートの中からidを取得
        Folderのid、日報名が必要
    2. idの中にあるワークシートを名前(year/mm)により取得
    3. dfへ
    """

    def get_df_from_ss(self) -> pd.DataFrame:
        try:
            spreadsheet = SpreadSheets.SpreadSheets()
            ss_id = spreadsheet.get_spreadsheet_id_by_name(
                folder_id="1zPbemG8PafxBNUAmsIkqTNM_4RSBh3lZ",
                spreadsheet_name="日報_all"
            )
            ss = spreadsheet.get_spreadsheet_by_id(ss_id)
            worksheet = ss.worksheet("シート1")
            df = spreadsheet.get_df_from_worksheet(worksheet)

            if "日付" in df.columns:
                # フォーマット指定を外して自動判別に任せる
                df["日付"] = pd.to_datetime(df["日付"], errors="coerce")
                df = df.dropna(subset=["日付"])   # 変換失敗行を除去
                df = df.set_index("日付")
            df = df.replace(r"^\s*$", np.nan, regex=True)
            return df
        except Exception as e:
            print(f"get_df_from_ss でエラー: {e}")
            return pd.DataFrame()


        
    def get_df_by_date(
            self,
            date: str
            ) -> pd.DataFrame:
        try:
            date = date.replace('_', '/')
            spreadsheet = SpreadSheets.SpreadSheets()
            # ディレクトリ内のCSVファイルをリストアップ
            id = spreadsheet.get_spreadsheet_id_by_name(
                folder_id="1zPbemG8PafxBNUAmsIkqTNM_4RSBh3lZ",
                spreadsheet_name=f"新店舗_日報_{date[:4]}"
            )
            ss = spreadsheet.get_spreadsheet_by_id(id)
            worksheet = ss.worksheet(date)
            df = spreadsheet.get_df_from_worksheet(worksheet)
            if "日付" in df.columns:
                df = df.set_index("日付")
                # インデックスが空（空文字または空白のみ）の行を削除
                df = df[df.index.astype(str).str.strip() != ""]
            df = df.replace(r'^\s*$', np.nan, regex=True)
            return df
        except:
            return pd.DataFrame()
        
    def set_all_daily_report_dic(self) -> dict:
        month_list = self.get_month_list()

        df = self.get_df_from_ss()
        if df.empty:
            return {}

        df_daily_report_dic: dict[str, dict[str, pd.DataFrame]] = {}

        for ym in month_list:
            year_str, month_str = ym.split("_")
            y = int(year_str)
            m = int(month_str)

            # 年のキーがなければ用意
            df_daily_report_dic.setdefault(year_str, {})

            # DatetimeIndex を使ってフィルタ
            mask = (df.index.year == y) & (df.index.month == m)
            sub_df = df.loc[mask]

            df_daily_report_dic[year_str][month_str] = sub_df

        return df_daily_report_dic
    

    def get_all_daily_report_dic(self) -> dict:
        """
        月ごとのCSVデータを取得し、convert_daily_report_dataを適用する。
        Returns:
            dict: 年ごとの月別変換済みデータフレーム辞書
        """
        # データをセット
        __df_dic = self.set_all_daily_report_dic()

        # すべてのDataFrameにconvert_daily_report_dataを適用
        for year, months in __df_dic.items():
            for month, df in months.items():
                try:
                    # DataFrameを変換
                    __df_dic[year][month] = self.convert_daily_report_data(df)
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        # print(df_dic)
        return __df_dic

    def get_all_weekly_report_dic(self):
        df_weekday_dic = {}
        # データをセット
        __df_dic = self.df_dic

        # すべてのDataFrameに `convert_daily_report_data` を適用
        for year, months in __df_dic.items():
            if year not in df_weekday_dic:
                df_weekday_dic[year] = {}  # 年ごとに辞書を作成
            for month, df in months.items():
                try:
                    # 月ごとの辞書を作成
                    df_weekday_dic[year][month] = (
                        df.groupby('曜日').mean()
                        .reindex(index=['水', '木', '金', '土', '日', '祝日'])
                        .fillna(0)
                    )
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        # print(df_weekday_dic)
        return df_weekday_dic
    

    def weekly_get_left_and_right_diff(self, df_left: pd.DataFrame, df_right: pd.DataFrame, option: str):
        df_diff_dic = {}
        
        # インデックスが一致することを確認
        if not df_left.index.equals(df_right.index):
            print("Warning: Indices do not match!")
            # 共通インデックスを取得
            common_index = df_left.index.intersection(df_right.index)
            df_left = df_left.loc[common_index]
            df_right = df_right.loc[common_index]
        
        for col in df_right.index:
            # 左右の売上データを取得
            left_value = df_left[option].get(col, 0)  # colがない場合は0を使う
            right_value = df_right[option].get(col, 0)  # colがない場合は0を使う
            
            # 差分計算
            if left_value != 0:
                ratio = ((right_value - left_value) / left_value) * 100  # 増減の割合
            else:
                ratio = 0  # left_valueが0の場合は、差分が計算できないので0とする
            
            # 増減の表示文字列を決定
            if ratio > 0:
                change = f"{round(ratio, 2)}%"
            elif ratio < 0:
                change = f"-{round(abs(ratio), 2)}%"
            else:
                change = "No change"
            
            df_diff_dic[col] = change
        return df_diff_dic


    def get_df_from_dic(self, date: str):
        # 年と月を取得
        year = date[:4]
        month = date.split('_')[1]

        # 辞書に年ごとのエントリを初期化
        if year not in self.df_dic:
            self.df_dic[year] = {}

        try:
            df = self.df_dic[year][month]
            return df
        except Exception as e:
                print(f"エラーが発生しました: {e}")