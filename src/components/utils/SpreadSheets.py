
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

class SpreadSheets:
    def __init__(self):
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        try:
            # secrets から認証情報を取得
            credentials_dict = st.secrets["GOOGLE_CLOUD_KEY"]  # json.loads() は不要
            c = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        except:
            # ローカルの JSON ファイルを使用
            json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/config/mitsuka-streamlit-9d15df827484.json"))
            c = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)

        self.gs = gspread.authorize(c)

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