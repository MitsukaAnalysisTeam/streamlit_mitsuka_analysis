from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import jpholiday
import japanize_matplotlib
import os
import re 
 
japanize_matplotlib.japanize()
'''
データの処理を行うファイル。
'''
class DailyReportAnalysisUtils:
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

    def __add_df_jpholiday(      
            self, 
            df: pd.DataFrame
            ) -> pd.DataFrame:
        date_month=df.index.tolist()
        for k in range(len(date_month)):
            date_month[k] = str(date_month[k])
            date_month[k] = datetime.strptime(str(date_month[k]), '%Y/%m/%d')
            date_month[k] = date(date_month[k].year, date_month[k].month, date_month[k].day)
        for d in range(len(date_month)):
            if jpholiday.is_holiday(date_month[d]):  # 祝日の場合はTrueを追加
                df.iat[d,0]='祝日'
        return df

    def __df_reindex_date(
            self,
            df: pd.DataFrame
            ) -> pd.DataFrame:
        date_index = []
        index_list = df.index.tolist()
        for i in range(len(index_list)):
            index_list[i] = index_list[i][5:] + '(' +df.iat[i,0]+ ')'
            date_index.append(index_list[i])
        df=df.set_axis(date_index, axis="index")
        return df
    
    def get_file_path_by_date(
            self,
            date: str
            )-> str: 
        # データフォルダのパス
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/daily_report"))
        
        # ディレクトリ内のCSVファイルをリストアップ
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]

        matched_file = [s for s in csv_files if re.match(f'.*{date}.*', s)]

        # ファイルが見つかった場合はフルパスを返す
        if matched_file:
            return os.path.join(data_dir, matched_file[0])
        
        # 見つからない場合は空文字列を返す
        return ""
    
    def set_all_daily_report_dic(
            self,
    ) -> dict:
        month_list = get_month_list()
        df_daily_report_dic = {}
        for date in month_list:
            file_path = self.get_file_path_by_date(date)
            # 年と月を取得
            year = date[:4]
            month = date.split('_')[1]

            # 辞書に年ごとのエントリを初期化
            if year not in df_daily_report_dic:
                df_daily_report_dic[year] = {}

            # CSVを読み込み、辞書に追加
            try:
                df = pd.read_csv(file_path,index_col = 0)
                df_daily_report_dic[year][month] = df
            except Exception as e:
                    print(f"エラーが発生しました: {file_path}, {e}")
        
        # print(df_daily_report_dic)
        return df_daily_report_dic
    
    def get_all_daily_report_dic(self) -> dict:
        """
        月ごとのCSVデータを取得し、convert_daily_report_dataを適用する。
        Returns:
            dict: 年ごとの月別変換済みデータフレーム辞書
        """
        # データをセット
        df_dic = self.set_all_daily_report_dic()

        # すべてのDataFrameにconvert_daily_report_dataを適用
        for year, months in df_dic.items():
            for month, df in months.items():
                try:
                    # DataFrameを変換
                    df_dic[year][month] = self.convert_daily_report_data(df)
                except Exception as e:
                    print(f"エラーが発生しました: 年={year}, 月={month}, {e}")
        # print(df_dic)
        return df_dic

    def get_all_weekly_report_dic(self):
        df_weekday_dic = {}
        # データをセット
        df_dic = self.get_all_daily_report_dic()

        # すべてのDataFrameに `convert_daily_report_data` を適用
        for year, months in df_dic.items():
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
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/hourly_report/customer_num"))
        
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
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/processed/hourly_report/sales_sum"))
        
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



