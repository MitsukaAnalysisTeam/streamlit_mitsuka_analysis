import streamlit as st
import pandas as pd
from datetime import datetime
import os

# フィードバックを保存するファイル名
FEEDBACK_FILE = data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw/feedback/feedback.csv"))

def save_feedback(question):
    """意見をCSVファイルに保存"""
    # 現在の日付を取得
    current_date = datetime.now().strftime("%Y-%m-%d")

    # ファイルが存在するか確認
    if os.path.exists(FEEDBACK_FILE):
        df = pd.read_csv(FEEDBACK_FILE)
    else:
        df = pd.DataFrame(columns=["日付", "意見"])

    # 新しいデータを追加
    new_data = pd.DataFrame({"日付": [current_date], "意見": [question]})
    df = pd.concat([df, new_data], ignore_index=True)

    # CSVファイルとして保存
    df.to_csv(FEEDBACK_FILE, index=False)

def show():
    st.write("ホームページ")

    # 質問受付フォームの追加
    with st.form(key="question_form"):
        question = st.text_area("意見がある場合はここへ↓↓\nみなさんのフィードバックでより良い分析ページを作っていきましょう！")
        submit_button = st.form_submit_button(label="送信")

    if submit_button:
        if question:
            save_feedback(question)  # CSVに保存
            st.success(f"意見を受け付けました！\n\n**質問:** {question}")
        else:
            st.error("すべての項目を入力してください。")

