import streamlit as st
import sys
import os

# プロジェクトのルートディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 各ページモジュールをインポート
from src.pages import home, analytics

# タブの作成
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["ホーム", 
                                                         "日報分析",
                                                         "時間別分析", 
                                                         "月別分析",
                                                         "曜日別分析",
                                                         "夜ラーメン",
                                                         "昼ラーメン",
                                                         "アルコール"])

# タブ1: Home
with tab1:
    st.title("みつか坊主 - ホーム")
    home.show()

# タブ2: Analytics
with tab2:
    st.title("みつか坊主 - 日別分析")
    analytics.daily_report_analysis()

with tab3:
    '''
    未実装
    '''

    st.title("みつか坊主 - 時間別分析")
    analytics.hourly_report_analysis()

with tab4:
    st.title("みつか坊主 - 月別分析")
    analytics.monthly_report_analysis()

with tab5:
    st.title("みつか坊主 - 曜日別分析")
    analytics.weekly_report_analysis()

with tab6:
    '''
    未実装
    '''

    st.title("みつか坊主 - 夜ラーメン")
    analytics.night_ramen_analysis()
    
with tab7:
    '''
    未実装
    '''

    st.title("みつか坊主 - 昼ラーメン")
    analytics.lunch_ramen_analysis()


with tab8:
    '''
    未実装
    '''

    st.title("みつか坊主 - アルコール")
    analytics.alchohol_analysis()