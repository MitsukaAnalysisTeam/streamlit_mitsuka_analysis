import sys
import os

# src ディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 必要なモジュール
import components.utils.Json as Json
import pandas as pd
# データフォルダのパス
print(Json.read_json_file(filepath='data/json/lunch.json'))
