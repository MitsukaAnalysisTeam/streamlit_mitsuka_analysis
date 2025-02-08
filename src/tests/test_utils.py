import sys
import os

# src ディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 必要なモジュール
import src.components.utils as utils
# データフォルダのパス
# data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/daily_report"))

spreadsheet = utils.SpreadSheets()

spreadsheet.get_sheet()