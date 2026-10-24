"""common.py の単体テスト。API は呼ばず、合成した応答で変換・正規化・振り分けを確認する。

使い方: python benchmarks/nl_chart/test_common.py
"""
import json
from pathlib import Path

import common as c
from src.components.assistant.catalog import CATALOG, HIGHLIGHTS, NONE_OF_THESE


def _all_arg_count():
    return sum(len(ch.args) for ch in c.CHARTS)


def test_questions_cover_catalog():
    qs = c.build_questions()
    assert len(qs) == 3 + _all_arg_count()
    assert len({q.name for q in qs}) == len(qs)
    chart_q = next(q for q in qs if q.name == c.CHART)
    assert [v for v, _ in chart_q.options] == [ch.id for ch in c.CHARTS]
    with_none = next(q for q in c.build_questions(with_none=True) if q.name == c.CHART)
    assert with_none.options[-1][0] == NONE_OF_THESE


def test_shuffle_changes_order_but_not_content():
    base = c.build_questions()
    shuffled = c.build_questions(seed=1)
    for a, b in zip(base, shuffled):
        assert a.name == b.name
        assert sorted(a.options) == sorted(b.options)
    assert [q.options for q in base] != [q.options for q in shuffled]
    # 同じ seed は同じ順序
    assert [q.options for q in c.build_questions(seed=1)] == [q.options for q in shuffled]


def test_request_bodies_are_json_serializable():
    state = c.build_state("先月のランチの売上", None)
    qs = c.build_questions()
    jev = c.to_jev_request("jev-latest", state, qs)
    dec = c.to_decisions_request("gpt-6-luna", state, qs)
    json.dumps(jev, ensure_ascii=False)
    json.dumps(dec, ensure_ascii=False)
    assert jev["questions"][c.ANSWERABLE]["type"] == "noul"
    assert jev["questions"][c.CHART]["type"] == "choice"
    assert dec["questions"][0] == {"type": "predicate", "name": c.ANSWERABLE,
                                   "instructions": qs[0].instructions}
    assert all(len(q["choices"]) >= 1 for q in dec["questions"][1:])


def _jev_choice(choice, conf, probs=None):
    return {"type": "choice", "choice": choice, "confidence": conf,
            "probabilities": probs or {choice: conf}}


def _jev_response(chart_id, conf=0.9, answerable=0.95, highlight="none", arg_overrides=None):
    answers = {
        c.ANSWERABLE: {"type": "noul", "noul": answerable},
        c.CHART: _jev_choice(chart_id, conf),
        c.HIGHLIGHT: _jev_choice(highlight, conf),
    }
    for ch in c.CHARTS:  # 全チャート分の引数に、既定値を返す
        for a in ch.args:
            value = (arg_overrides or {}).get((ch.id, a.name), a.default)
            answers[c.arg_question_name(ch.id, a.name)] = _jev_choice(value, conf)
    return {"model": "jev-latest", "answers": answers, "usage": {"input_tokens": 1, "output_tokens": 0}}


def test_jev_parse_and_assemble():
    resp = _jev_response("ramen_pie", arg_overrides={("ramen_pie", "slot"): "夜"})
    pred = c.assemble_judge_prediction(c.parse_jev_response(resp))
    assert pred.chart_id == "ramen_pie"
    assert pred.args == {"slot": "夜", "mode": "販売数"}  # 選ばれたチャートの分だけ拾う
    assert set(pred.arg_confs) == {"slot", "mode"}
    assert pred.invalid is None


def test_decisions_parse_matches_jev():
    jev = c.parse_jev_response(_jev_response("daily_bar"))
    dec_resp = {"answers": []}
    for name, a in jev.items():
        if a.kind == "predicate":
            dec_resp["answers"].append({"type": "predicate", "name": name, "probability": a.probability})
        else:
            dec_resp["answers"].append({
                "type": "choice", "name": name, "choice": a.choice, "confidence": a.confidence,
                "probabilities": [{"value": k, "probability": v} for k, v in a.probabilities.items()],
            })
    assert c.parse_decisions_response(dec_resp) == jev


def test_refusal_goes_to_fallback():
    resp = _jev_response("daily_bar")
    pred = c.assemble_judge_prediction({"x": c.NormAnswer("refusal")})
    assert pred.refused and c.route(pred) == "fallback"
    assert resp  # 形の確認のみ


def test_route_rules():
    def pred(chart_conf=0.9, answerable=0.95, hl_conf=0.9):
        p = c.assemble_judge_prediction(c.parse_jev_response(_jev_response("daily_bar", conf=chart_conf, answerable=answerable)))
        p.highlight_conf = hl_conf
        return p

    assert c.route(pred()) == "run"
    assert c.route(pred(chart_conf=0.6)) == "ask_back"
    assert c.route(pred(chart_conf=0.3)) == "fallback"
    assert c.route(pred(answerable=0.1)) == "reject"  # 規則 1 が先
    assert c.route(pred(answerable=0.4)) == "fallback"  # 微妙なとき
    # 強調だけが低い場合: 含めるなら聞き返し／LLM、外すなら実行
    assert c.route(pred(hl_conf=0.3)) == "fallback"
    assert c.route(pred(hl_conf=0.3), include_highlight=False) == "run"


def test_none_of_these_goes_to_fallback():
    resp = _jev_response(NONE_OF_THESE)
    pred = c.assemble_judge_prediction(c.parse_jev_response(resp))
    assert pred.invalid is None and pred.args == {}
    assert c.route(pred) == "fallback"
    # 答えられる確率が低ければ、「どれも当てはまらない」でも対応外が先
    low = c.assemble_judge_prediction(c.parse_jev_response(_jev_response(NONE_OF_THESE, answerable=0.05)))
    assert c.route(low) == "reject"


def test_invalid_chart_id():
    pred = c.assemble_judge_prediction(c.parse_jev_response(_jev_response("weather_map")))
    assert pred.invalid and c.route(pred) == "fallback"


def test_ask_back_candidates_from_probs():
    p = c.Prediction(chart_probs={"daily_bar": 0.4, NONE_OF_THESE: 0.3, "monthly_sum": 0.2, "yearly_bar": 0.1})
    assert c.top_chart_candidates(p, 2) == ["daily_bar", "monthly_sum"]


def test_tools():
    tools = c.build_tools()
    names = [t["name"] for t in tools]
    assert names == [ch.id for ch in c.CHARTS] + [c.ASK_BACK_TOOL, c.REJECT_TOOL]
    for t in tools:
        json.dumps(t, ensure_ascii=False)
        assert t["input_schema"]["additionalProperties"] is False
        assert set(t["input_schema"]["required"]) == set(t["input_schema"]["properties"])
    ramen = next(t for t in tools if t["name"] == "ramen_pie")
    assert ramen["input_schema"]["properties"]["slot"]["enum"] == ["昼", "夜", "深夜", "全体"]
    assert ramen["input_schema"]["properties"]["highlight"]["enum"] == list(HIGHLIGHTS)


def test_parse_tool_call():
    ok = c.parse_tool_call("ramen_pie", {"slot": "夜", "mode": "売上", "highlight": "max"})
    assert (ok.action, ok.chart_id, ok.args, ok.highlight, ok.invalid) == (
        "run", "ramen_pie", {"slot": "夜", "mode": "売上"}, "max", None)
    bad_value = c.parse_tool_call("ramen_pie", {"slot": "朝", "mode": "売上", "highlight": "none"})
    assert bad_value.invalid
    bad_chart = c.parse_tool_call("pie_of_everything", {"highlight": "none"})
    assert bad_chart.invalid
    bad_hl = c.parse_tool_call("daily_bar", {"metric": "売上", "highlight": "top3"})
    assert bad_hl.invalid
    ask = c.parse_tool_call(c.ASK_BACK_TOOL, {"candidates": ["daily_bar", "nonexistent"]})
    assert (ask.action, ask.candidates) == ("ask_back", ["daily_bar"])
    assert c.parse_tool_call(c.REJECT_TOOL, {"reason": "天気"}).action == "reject"


def test_load_env(tmp_path=None):
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / ".env"
        f.write_text('# c\nNLTEST_A=abc\nNLTEST_B="q"\nNLTEST_C=\n', encoding="utf-8")
        os.environ.pop("NLTEST_A", None)
        os.environ.pop("NLTEST_B", None)
        os.environ["NLTEST_C"] = "keep"
        c.load_env(f)
        assert os.environ["NLTEST_A"] == "abc" and os.environ["NLTEST_B"] == "q"
        assert os.environ["NLTEST_C"] == "keep"  # 既存の環境変数が優先
        for k in ("NLTEST_A", "NLTEST_B", "NLTEST_C"):
            os.environ.pop(k, None)


def test_dataset_questions_build():
    """全質問で state・リクエストが作れる（previous_request つきを含む）。"""
    rows = [json.loads(l) for l in (Path(__file__).with_name("dataset.jsonl")).read_text(encoding="utf-8").splitlines() if l]
    qs = c.build_questions()
    for r in rows:
        state = c.build_state(r["question"], r["previous_request"])
        json.dumps(c.to_jev_request("jev-latest", state, qs), ensure_ascii=False)
        assert r["question"] in c.build_user_message(r["question"], r["previous_request"])


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("ok", name)
    print(f"{len(tests)} tests passed")
