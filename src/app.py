import streamlit as st
import sys
import os

# プロジェクトのルートディレクトリをモジュール検索パスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pages import home, analytics

# サイドバーでページ切り替え
page = st.selectbox("ページを選択", ["Home", "Analytics"])

st.title("みつか坊主分析ページ")

if page == "Home":
    analytics.show()
elif page == "Analytics":
    home.show()
