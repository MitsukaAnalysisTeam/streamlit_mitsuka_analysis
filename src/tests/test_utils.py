import os
import re

# データフォルダのパス
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/daily_report"))

# ディレクトリ内のCSVファイルをリストアップ
csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
date = "2024_5"

l_re_match = [s for s in csv_files if re.match(f'.*{date}.*', s)]

print(l_re_match[0])


print(csv_files,date)
