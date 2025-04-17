import streamlit as st
import sys
import os

# プロジェクトのルートディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# 各ページモジュールをインポート
from components.pages import home
from components.pages import analytics

# タブの名前リスト
tab_names = [
    "ホーム",
    "日報分析",
    "時間別分析",
    "月別分析",
    "曜日別分析",
    "夜ラーメン",
    "昼ラーメン",
    "アルコール"
]

# st.tabs を使ってタブを作成
tabs = st.tabs(tab_names)

# 各タブごとに内容を記述
with tabs[0]:
    st.title("みつか坊主 - ホーム")
    home.show()

with tabs[1]:
    st.title("みつか坊主 - 日別分析")
    analytics.daily_report_analysis()

with tabs[2]:
    st.title("みつか坊主 - 時間別分析")
    analytics.hourly_report_analysis()

with tabs[3]:
    st.title("みつか坊主 - 月別分析")
    analytics.monthly_report_analysis()

with tabs[4]:
    st.title("みつか坊主 - 曜日別分析")
    analytics.weekly_report_analysis()

with tabs[5]:
    st.title("みつか坊主 - 夜ラーメン")
    st.write("未実装")
    analytics.night_ramen_analysis()

with tabs[6]:
    st.title("みつか坊主 - 昼ラーメン")
    st.write("未実装")
    analytics.lunch_ramen_analysis()

with tabs[7]:
    st.title("みつか坊主 - アルコール")
    st.write("未実装")
    analytics.alchohol_analysis()
