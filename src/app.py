import streamlit as st
import sys
import os

# プロジェクトのルートディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from components.pages import home, analytics

# サイドバーにページ選択メニューを作成
st.sidebar.title("ナビゲーション")
page = st.sidebar.radio(
    label="ページを選択",
    options=[
        "ホーム",
        "日報分析",
        "時間別分析",
        "月別分析",
        "曜日別分析",
        "夜ラーメン",
        "昼ラーメン",
        "アルコール"
    ]
)

# 選択に応じて該当ページを表示
if page == "ホーム":
    st.title("みつか坊主 - ホーム")
    home.show()

elif page == "日報分析":
    st.title("みつか坊主 - 日別分析")
    analytics.daily_report_analysis()

elif page == "時間別分析":
    st.title("みつか坊主 - 時間別分析")
    analytics.hourly_report_analysis()

elif page == "月別分析":
    st.title("みつか坊主 - 月別分析")
    analytics.monthly_report_analysis()

elif page == "曜日別分析":
    st.title("みつか坊主 - 曜日別分析")
    analytics.weekly_report_analysis()

elif page == "夜ラーメン":
    st.title("みつか坊主 - 夜ラーメン")
    analytics.night_ramen_analysis()

elif page == "昼ラーメン":
    st.title("みつか坊主 - 昼ラーメン")
    analytics.lunch_ramen_analysis()

elif page == "アルコール":
    st.title("みつか坊主 - アルコール")
    analytics.alchohol_analysis()
