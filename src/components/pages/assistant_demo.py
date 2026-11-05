"""「AIに聞く」の動作確認用デモ。判断役（Jev）だけで動かし、LLM に回る場合は表示だけする。

グラフの描画はまだつながっていない（カタログの render が未実装）。
ベンチマークのコードを流用しているため、本実装で src/components/assistant/ に移す。
"""
import os
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st

_BENCH = Path(__file__).resolve().parents[3] / "benchmarks" / "nl_chart"
if str(_BENCH) not in sys.path:
    sys.path.insert(0, str(_BENCH))

import common as c  # noqa: E402
from adapters.http_judges import JevAdapter  # noqa: E402
from src.components.assistant.catalog import CATALOG, NONE_OF_THESE  # noqa: E402

EXAMPLES = [
    "先月のランチの売上を円グラフで",
    "深夜のラーメンで何が一番売れてる？",
    "売上見せて",
    "明日の天気は？",
    "ビールの平均杯数の月別推移",
    "今年って去年よりお客さん来てる？",
]

ACTION_LABEL = {
    "run": ("✅ そのまま実行", "success"),
    "ask_back": ("❓ 聞き返し", "warning"),
    "reject": ("🚫 対応外", "error"),
    "fallback": ("🤖 LLM にフォールバック（このデモでは呼ばない）", "info"),
}


def _api_key() -> str:
    c.load_env()
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        try:
            key = st.secrets.get("TYPESAFE_API_KEY")
        except Exception:
            key = None
    return key or ""


def _chart_name(chart_id: str) -> str:
    return f"{chart_id}（{CATALOG[chart_id].description}）" if chart_id in CATALOG else str(chart_id)


def show():
    st.caption("質問を入れると、Jev がどのグラフ・どの設定だと判断したか、その自信（confidence）と、振り分け結果を表示します。")

    key = _api_key()
    if not key:
        st.error("`.env` に `TYPESAFE_API_KEY` がありません（`.env.example` を参照）。")
        return

    with st.sidebar.expander("デモの設定", expanded=False):
        model = st.selectbox("Jev のバージョン", ["jev-latest", "jev-preview"])
        with_none = st.checkbox("「どれも当てはまらない」の選択肢を足す", value=False)
        include_hl = st.checkbox("強調の自信も判定に含める", value=True)
        t_reject = st.slider("対応外にする（答えられる確率がこれ未満）", 0.0, 1.0, 0.2, 0.05)
        t_llm = st.slider("LLM に回す（最も低い自信がこれ未満）", 0.0, 1.0, 0.5, 0.05)
        t_run = st.slider("そのまま実行する（最も低い自信がこれ以上）", 0.0, 1.0, 0.8, 0.05)

    st.write("例:")
    cols = st.columns(3)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 3].button(ex, key=f"ex{i}", width="stretch"):
            st.session_state["assistant_q"] = ex
    question = st.text_input("質問", key="assistant_q", placeholder="例: 先月のランチの売上を円グラフで")

    if not question.strip():
        return

    adapter = JevAdapter(model, api_key=key)
    row = {"question": question.strip(), "previous_request": None}
    t0 = time.time()
    try:
        res = adapter.call(row, with_none=with_none, seed=None)
    except Exception as e:  # noqa: BLE001
        st.error(f"Jev の呼び出しに失敗しました: {e}")
        return
    latency = time.time() - t0

    pred = c.assemble_judge_prediction(c.parse_jev_response(res["raw"]))
    action = c.route(pred, t_reject=t_reject, t_llm=t_llm, t_run=t_run, include_highlight=include_hl)
    label, kind = ACTION_LABEL[action]
    getattr(st, kind)(f"**{label}**")

    st.caption(f"応答 {latency:.2f} 秒 / 入力 {res['usage'].get('input_tokens', '?')} トークン")

    if action == "run":
        st.subheader("実行するグラフ")
        st.write(f"**{_chart_name(pred.chart_id)}**")
        st.json({"args": pred.args, "highlight": pred.highlight})
        st.info("ここに実際のグラフが出る予定です（描画はまだつないでいません）。")
    elif action == "ask_back":
        st.subheader("聞き返しの候補")
        for cid in c.top_chart_candidates(pred):
            st.write(f"- {_chart_name(cid)}（{pred.chart_probs.get(cid, 0):.0%}）")
    elif action == "fallback":
        st.subheader("Jev の第一候補（自信が低いため LLM に回す）")
        st.write(f"**{_chart_name(pred.chart_id)}**" if pred.chart_id else "なし")
        if pred.invalid:
            st.warning(f"カタログに収まらない出力: {pred.invalid}")

    st.subheader("Jev の判断の中身")
    rows = [{"項目": "答えられる確率", "答え": "", "自信": pred.answerable}]
    rows.append({"項目": "グラフ", "答え": pred.chart_id, "自信": pred.chart_conf})
    for name, conf in pred.arg_confs.items():
        rows.append({"項目": f"引数: {name}", "答え": pred.args.get(name), "自信": conf})
    rows.append({"項目": "強調", "答え": pred.highlight, "自信": pred.highlight_conf})
    df = pd.DataFrame(rows)
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={"自信": st.column_config.ProgressColumn("自信", min_value=0.0, max_value=1.0, format="%.2f")})

    if pred.chart_probs:
        top = sorted(pred.chart_probs.items(), key=lambda kv: kv[1], reverse=True)[:5]
        st.write("グラフ候補の確率（上位 5 件）")
        st.bar_chart(pd.DataFrame({"確率": [v for _, v in top]}, index=[k for k, _ in top]))

    with st.expander("Jev の生の応答"):
        st.json(res["raw"])
