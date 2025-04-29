import sys
import os

# src ディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 必要なモジュール
import components.utils.SpreadSheets as SS
import pandas as pd
# データフォルダのパス
# data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/daily_report"))

spreadsheet = SS.SpreadSheets()

id = spreadsheet.get_spreadsheet_id_by_name(
    folder_id="1zPbemG8PafxBNUAmsIkqTNM_4RSBh3lZ",
    spreadsheet_name="新店舗_日報_2025"
)
print(id)
ss = spreadsheet.get_spreadsheet_by_id(id)
worksheet = ss.worksheet("2025/1")
df = spreadsheet.get_df_from_worksheet(worksheet)
print(df)
df.to_csv("test.csv", index=False)
