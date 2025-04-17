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
from googleapiclient.discovery import build

japanize_matplotlib.japanize()

class SpreadSheets:
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        try:
            # st.secrets が存在し、かつ "GOOGLE_CLOUD_KEY" がある場合はそれを使用
            if hasattr(st, "secrets") and "GOOGLE_CLOUD_KEY" in st.secrets:
                credentials_dict = st.secrets["GOOGLE_CLOUD_KEY"]
                c = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        except Exception as e:
            # st.secrets が利用できなかった場合はローカルの JSON ファイルを使用
            json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/config/mitsuka-streamlit-9d15df827484.json"))
            c = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)

        self.gs = gspread.authorize(c)
        # Drive API を利用するためのサービスを初期化
        self.drive = build("drive", "v3", credentials=c)

    def write_feedback(self, date, text: str):
        try:
            # TODO: .envファイルに格納する
            SPREADSHEET_KEY = '1fD72LURrehID1rGWbDn2bzD0Okt0LMORMM2dHJQlXbs'
            worksheet = self.gs.open_by_key(SPREADSHEET_KEY).worksheet("シート1")
            
            # スプレッドシートのデータを取得
            data = worksheet.get_all_values()

            # データの有無を確認
            if not data:
                df = pd.DataFrame(columns=["date", "text"])
            else:
                df = pd.DataFrame(data[1:], columns=data[0])

            # 新しいデータを追加
            new_row = {"date": str(date), "text": text}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # NaN を空文字列に変換
            df = df.fillna("")

            # 更新
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())

        except Exception as e:
            print(f"エラーが発生しました: {e}")

    def get_spreadsheet_id_by_name(self, folder_id: str, spreadsheet_name: str) -> str:
        """
        指定したフォルダ内から、指定のスプレッドシート名で一致するファイルを検索し、
        そのスプレッドシートの ID を返します。見つからなかった場合は空文字列を返します。
        """
        query = (
            f"'{folder_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.spreadsheet' and "
            f"name = '{spreadsheet_name}'"
        )
        try:
            response = self.drive.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            files = response.get('files', [])
            if files:
                # 同じ名前のファイルが複数存在する場合は最初のものを返す
                return files[0]['id']
            else:
                print("指定された名前のスプレッドシートは見つかりませんでした。")
                return ""
        except Exception as e:
            print(f"get_spreadsheet_id_by_name でエラーが発生しました: {e}")
            return ""
        
    def get_spreadsheet_by_id(self, spreadsheet_id: str):
        """
        指定されたスプレッドシートIDからスプレッドシートを開き、
        指定のワークシート名のワークシートを返します。
        
        引数:
            spreadsheet_id (str): 対象のスプレッドシートのID
            worksheet_name (str): 取得したいワークシートの名前
        
        戻り値:
            worksheet: 指定されたワークシート。存在しない場合は None を返します。
        """
        try:
            # gspread を用いてスプレッドシートを開く
            spreadsheet = self.gs.open_by_key(spreadsheet_id)
            return spreadsheet
        except Exception as e:
            print(f"get_worksheet_by_id でエラーが発生しました: {e}")
            return None
        
    def get_worksheet_by_name(self, spreadsheet, worksheet_name: str):
        """
        指定されたスプレッドシートIDからスプレッドシートを開き、
        指定のワークシート名のワークシートを返します。

        引数:
            spreadsheet_id (str): 対象のスプレッドシートのID
            worksheet_name (str): 取得したいワークシートの名前

        戻り値:
            worksheet: 指定されたワークシート。存在しない場合は None を返します。
        """
        try:
            # 指定のワークシートを取得
            worksheet = spreadsheet.worksheet(worksheet_name)
            return worksheet
        except Exception as e:
            print(f"get_worksheet_by_id でエラーが発生しました: {e}")
            return None

    def get_df_from_worksheet(self, worksheet):
        """
        指定されたワークシートからデータを取得し、データフレームに変換します。

        引数:
            worksheet: 対象のワークシート

        戻り値:
            df: データフレーム。データが存在しない場合は空のデータフレームを返します。
        """
        try:
            # データを取得
            data = worksheet.get_all_values()
            if not data:
                return pd.DataFrame()
            # データフレームに変換
            df = pd.DataFrame(data[1:], columns=data[0])
            return df
        except Exception as e:
            print(f"get_df_from_worksheet でエラーが発生しました: {e}")
            return pd.DataFrame()