"""アダプタと run.py の単体テスト。API は呼ばず、偽の応答で保存までの流れを確認する。

使い方: python benchmarks/nl_chart/test_run.py
"""
import io
import json
from types import SimpleNamespace

import common as c
import run
from adapters.claude import ClaudeAdapter
from adapters.http_judges import DecisionsAdapter, JevAdapter
from adapters.openai_llm import OpenAILLMAdapter, to_responses_tools
from test_common import _jev_response

ROWS = run.load_dataset("dev", limit=3)


def _fake_jev_post(url, headers, body):
    assert url.endswith("/v1/systemone") and headers["Authorization"] == "Bearer k"
    assert set(body) == {"model", "state", "questions"}
    return _jev_response("daily_bar")


def _fake_decisions_post(url, headers, body):
    assert url.endswith("/v1/decisions") and body["model"] == "gpt-6-luna"
    jev = c.parse_jev_response(_jev_response("daily_bar"))
    answers = []
    for name, a in jev.items():
        if a.kind == "predicate":
            answers.append({"type": "predicate", "name": name, "probability": a.probability})
        else:
            answers.append({"type": "choice", "name": name, "choice": a.choice, "confidence": a.confidence,
                            "probabilities": [{"value": k, "probability": v} for k, v in a.probabilities.items()]})
    return {"answers": answers}


class _FakeClient:
    def __init__(self, blocks, stop_reason="tool_use"):
        self.calls = []
        self.messages = SimpleNamespace(create=self._create)
        self._blocks, self._stop = blocks, stop_reason

    def _create(self, **kw):
        self.calls.append(kw)
        return SimpleNamespace(content=self._blocks, stop_reason=self._stop,
                               usage=SimpleNamespace(input_tokens=100, output_tokens=20))


def _tool_block(name, inp):
    return SimpleNamespace(type="tool_use", name=name, input=inp)


def test_plan_counts():
    jobs = list(run.plan(ROWS, [False, True], [None, 1, 2], 2))
    assert len(jobs) == 3 * 2 * 3 * 2


def test_jev_end_to_end():
    adapter = JevAdapter("jev-latest", post=_fake_jev_post, api_key="k")
    buf = io.StringIO()
    ok, failed = run.run_all(adapter, list(run.plan(ROWS, [False], [None, 1], 1)), 2, buf)
    assert (ok, failed) == (6, 0)
    recs = [json.loads(l) for l in buf.getvalue().splitlines()]
    assert {r["shuffle_seed"] for r in recs} == {None, 1}
    pred = c.prediction_from_raw("jev", recs[0]["raw"])
    assert pred.chart_id == "daily_bar" and c.route(pred) == "run"


def test_decisions_end_to_end():
    adapter = DecisionsAdapter("gpt-6-luna", post=_fake_decisions_post, api_key="k")
    rec = run.run_one(adapter, ROWS[0], False, None, 0)
    assert "error" not in rec
    assert c.prediction_from_raw("decisions", rec["raw"]).chart_id == "daily_bar"


def test_errors_are_recorded_not_raised():
    def boom(url, headers, body):
        raise RuntimeError("503")

    rec = run.run_one(JevAdapter("jev-latest", post=boom, api_key="k"), ROWS[0], False, None, 0)
    assert rec["error"].startswith("RuntimeError") and "raw" not in rec


def test_claude_request_and_parse():
    # 先頭が思考ブロックでも、type で tool_use を取り出す
    client = _FakeClient([SimpleNamespace(type="thinking"), _tool_block("ramen_pie", {"slot": "夜", "mode": "売上", "highlight": "none"})])
    adapter = ClaudeAdapter(client=client)
    rec = run.run_one(adapter, ROWS[0], False, None, 0)
    kw = client.calls[0]
    assert kw["model"] == "claude-haiku-5-5" and kw["tool_choice"] == {"type": "any"}
    assert kw["output_config"] == {"effort": "low"} and "temperature" not in kw
    assert kw["tools"][0]["strict"] is True
    pred = c.prediction_from_raw("claude", rec["raw"])
    assert (pred.action, pred.chart_id, pred.args["slot"]) == ("run", "ramen_pie", "夜")
    assert rec["usage"]["input_tokens"] == 100


def test_claude_refusal_and_no_tool():
    refusal = ClaudeAdapter(client=_FakeClient([], stop_reason="refusal"))
    rec = run.run_one(refusal, ROWS[0], False, None, 0)
    assert c.prediction_from_raw("claude", rec["raw"]).refused
    none = ClaudeAdapter(client=_FakeClient([SimpleNamespace(type="text")], stop_reason="end_turn"))
    rec = run.run_one(none, ROWS[0], False, None, 0)
    pred = c.prediction_from_raw("claude", rec["raw"])
    assert pred.invalid and pred.action is None


def _responses_post(output, status="completed"):
    def post(url, headers, body):
        post.body = body
        return {"status": status, "output": output,
                "usage": {"input_tokens": 900, "output_tokens": 30,
                          "input_tokens_details": {"cached_tokens": 800},
                          "output_tokens_details": {"reasoning_tokens": 0}}}
    return post


def test_openai_request_and_parse():
    call = {"type": "function_call", "name": "ramen_pie", "call_id": "x",
            "arguments": json.dumps({"slot": "夜", "mode": "売上", "highlight": "max"}, ensure_ascii=False)}
    post = _responses_post([{"type": "reasoning", "summary": []}, call])  # 先頭が思考でも拾う
    adapter = OpenAILLMAdapter(post=post, api_key="k")
    rec = run.run_one(adapter, ROWS[0], False, None, 0)
    b = post.body
    assert b["model"] == "gpt-6-luna" and b["tool_choice"] == "required" and b["reasoning"] == {"effort": "low"}
    assert b["tools"][0]["type"] == "function" and b["tools"][0]["strict"] is True and "input_schema" not in b["tools"][0]
    pred = c.prediction_from_raw("openai", rec["raw"])
    assert (pred.action, pred.chart_id, pred.highlight, pred.invalid) == ("run", "ramen_pie", "max", None)
    assert rec["usage"] == {"input_tokens": 900, "output_tokens": 30, "cached_tokens": 800, "reasoning_tokens": 0}


def test_openai_refusal_and_no_call():
    refusal = [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]
    rec = run.run_one(OpenAILLMAdapter(post=_responses_post(refusal), api_key="k"), ROWS[0], False, None, 0)
    assert c.prediction_from_raw("openai", rec["raw"]).refused
    text = [{"type": "message", "content": [{"type": "output_text", "text": "hi"}]}]
    rec = run.run_one(OpenAILLMAdapter(post=_responses_post(text), api_key="k"), ROWS[0], False, None, 0)
    assert c.prediction_from_raw("openai", rec["raw"]).invalid


def test_responses_tools_cover_all_chart_tools():
    tools = to_responses_tools(c.build_tools())
    assert [t["name"] for t in tools] == [t["name"] for t in c.build_tools()]
    assert all(t["parameters"]["additionalProperties"] is False for t in tools)


def test_make_adapter_effort():
    assert run.make_adapter("openai", "gpt-6-luna", "none").effort == "none"
    assert run.make_adapter("openai", "gpt-6-luna").effort == "low"
    assert run.make_adapter("jev", "jev-latest").model == "jev-latest"


def test_missing_key_stops_before_running():
    import os

    for k in ("TYPESAFE_API_KEY",):
        os.environ.pop(k, None)
    orig = c.load_env
    c.load_env = lambda *a, **k: None  # 手元の .env に左右されないようにする
    try:
        try:
            c.require_key("TYPESAFE_API_KEY")
        except SystemExit as e:
            assert ".env" in str(e)
        else:
            raise AssertionError("SystemExit が出るはず")
    finally:
        c.load_env = orig


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("ok", name)
    print(f"{len(tests)} tests passed")
