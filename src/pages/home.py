import streamlit as st
import pandas as pd
from datetime import datetime
import os
import src.components.utils as utils

# フィードバックを保存するファイル名
FEEDBACK_FILE = data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/feedback/feedback.csv"))

def save_feedback(question):
    """意見をCSVファイルに保存"""
    spreadsheet = utils.SpreadSheets()
    current_date = datetime.now()
    spreadsheet.write_feedback(date=current_date,text=question)

def show():
    st.write("ホームページ")

    # 質問受付フォームの追加
    with st.form(key="question_form"):
        question = st.text_area("意見がある場合はここへ↓↓\n\nみなさんのフィードバックでより良い分析ページを作っていきましょう！")
        submit_button = st.form_submit_button(label="送信")

    if submit_button:
        if question:
            save_feedback(question)  # CSVに保存
            st.success(f"意見を受け付けました！\n\n**質問:** {question}")
        else:
            st.error("すべての項目を入力してください。")

