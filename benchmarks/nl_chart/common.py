"""ベンチマーク共通の入出力。

チャートカタログ（`src/components/assistant/catalog.py`）から、
  - 判断役（Jev / OpenAI Decisions）への質問
  - フォールバック LLM のツール定義
を作り、どちらの出力も `Prediction` にそろえる。HTTP 呼び出しは含めない。
"""
from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.components.assistant.catalog import (  # noqa: E402
    CATALOG,
    CHARTS,
    HIGHLIGHTS,
    NONE_OF_THESE,
    NONE_OF_THESE_DESC,
    validate_request,
)

# ---------------------------------------------------------------- API キー


def load_env(path: Path = ROOT / ".env") -> None:
    """リポジトリ直下の .env を読み、未設定の環境変数だけ埋める（環境変数が優先）。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def require_key(name: str) -> str:
    load_env()
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} が未設定です。リポジトリ直下の .env に書いてください（.env.example を参照）")
    return value


# ---------------------------------------------------------------- 質問の組み立て


@dataclass
class Question:
    name: str
    kind: str  # "predicate" | "choice"
    instructions: str
    options: List[Tuple[str, str]] = field(default_factory=list)  # (値, 説明)。choice のみ


ANSWERABLE = "answerable"
CHART = "chart"
HIGHLIGHT = "highlight"
ARG_PREFIX = "arg__"


def arg_question_name(chart_id: str, arg: str) -> str:
    return f"{ARG_PREFIX}{chart_id}__{arg}"


def build_state(question: str, previous_request: Optional[dict]) -> Dict[str, Any]:
    """判断役に渡す state。期間の解釈は別処理なので、質問文はそのまま渡す。"""
    return {"question": question, "previous_request": previous_request}


def build_questions(with_none: bool = False, seed: Optional[int] = None) -> List[Question]:
    """判断役への質問一式を作る。全チャートの引数をまとめて聞き、選ばれたチャート分だけ使う。

    with_none: チャートの選択肢に「どれも当てはまらない」を足す（5.4 章の判定方式の比較用）。
    seed: 指定すると、選択肢の順序をシャッフルする（順序バイアスの確認用）。
    """
    rng = random.Random(seed) if seed is not None else None

    def ordered(options: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        options = list(options)
        if rng is not None:
            rng.shuffle(options)
        return options

    chart_options = [(c.id, c.description) for c in CHARTS]
    if with_none:
        chart_options.append((NONE_OF_THESE, NONE_OF_THESE_DESC))

    questions = [
        Question(
            ANSWERABLE,
            "predicate",
            "`question` は、店の売上データ（日報・時間別・月別・曜日別・年間・ラーメン・ランチ・アルコール）"
            "から作るグラフで答えられる質問か。天気・将来の予測・従業員・原価・競合店など、"
            "このデータにない内容は答えられない。",
        ),
        Question(
            CHART,
            "choice",
            "`question` に最も合うグラフを選ぶ。`previous_request` がある場合、"
            "`question` が「じゃあ夜は？」のように省略されていれば、直前のグラフを引き継いで考える。"
            "期間（先月・去年の夏など）はグラフの選択に関係しない。",
            ordered(chart_options),
        ),
        Question(
            HIGHLIGHT,
            "choice",
            "`question` の趣旨から、グラフ上で目立たせたい点の種類を選ぶ。"
            "「一番多い」「最も売れた」は最大、「一番少ない」「落ち込み」は最小、"
            "「伸びた」「減った」「比べて」は変化が最大の点、特に指定がなければ「目立たせない」。",
            ordered(list(HIGHLIGHTS.items())),
        ),
    ]
    for chart in CHARTS:
        for arg in chart.args:
            questions.append(
                Question(
                    arg_question_name(chart.id, arg.name),
                    "choice",
                    f"`question` が「{chart.description}」グラフについての質問だとして、"
                    f"{arg.description}を選ぶ。質問で指定されていなければ「{arg.default}」を選ぶ。"
                    "`previous_request` がある場合、省略された指定は直前の値を引き継ぐ。",
                    ordered(list(arg.options.items())),
                )
            )
    return questions


# ---------------------------------------------------------------- リクエスト本文


def to_jev_request(model: str, state: Dict[str, Any], questions: List[Question]) -> Dict[str, Any]:
    body_questions: Dict[str, Any] = {}
    for q in questions:
        if q.kind == "predicate":
            body_questions[q.name] = {"type": "noul", "instructions": q.instructions}
        else:
            body_questions[q.name] = {
                "type": "choice",
                "instructions": q.instructions,
                "criteria": {value: desc for value, desc in q.options},
            }
    return {"model": model, "state": state, "questions": body_questions}


def to_decisions_request(model: str, state: Dict[str, Any], questions: List[Question]) -> Dict[str, Any]:
    body_questions: List[Dict[str, Any]] = []
    for q in questions:
        if q.kind == "predicate":
            body_questions.append({"type": "predicate", "name": q.name, "instructions": q.instructions})
        else:
            body_questions.append(
                {
                    "type": "choice",
                    "name": q.name,
                    "instructions": q.instructions,
                    "choices": [{"value": v, "description": d} for v, d in q.options],
                }
            )
    # input は文字列か、メッセージ配列。state と同じ内容を JSON 文字列で渡す
    return {
        "model": model,
        "input": json.dumps(state, ensure_ascii=False),
        "questions": body_questions,
    }


# ---------------------------------------------------------------- 判断役の応答の正規化


@dataclass
class NormAnswer:
    kind: str  # "predicate" | "choice" | "refusal"
    probability: Optional[float] = None  # predicate
    choice: Optional[str] = None  # choice
    confidence: Optional[float] = None  # choice
    probabilities: Dict[str, float] = field(default_factory=dict)  # choice


def parse_jev_response(resp: Dict[str, Any]) -> Dict[str, NormAnswer]:
    out: Dict[str, NormAnswer] = {}
    for name, a in resp["answers"].items():
        if a["type"] == "noul":
            out[name] = NormAnswer("predicate", probability=a["noul"])
        elif a["type"] == "choice":
            out[name] = NormAnswer(
                "choice", choice=a["choice"], confidence=a["confidence"], probabilities=dict(a["probabilities"])
            )
        else:
            out[name] = NormAnswer("refusal")
    return out


def parse_decisions_response(resp: Dict[str, Any]) -> Dict[str, NormAnswer]:
    out: Dict[str, NormAnswer] = {}
    for a in resp["answers"]:
        if a["type"] == "predicate":
            out[a["name"]] = NormAnswer("predicate", probability=a["probability"])
        elif a["type"] == "choice":
            out[a["name"]] = NormAnswer(
                "choice",
                choice=a["choice"],
                confidence=a["confidence"],
                probabilities={p["value"]: p["probability"] for p in a["probabilities"]},
            )
        else:
            out[a["name"]] = NormAnswer("refusal")
    return out


# ---------------------------------------------------------------- 予測（モデル共通の出力）


@dataclass
class Prediction:
    action: Optional[str] = None  # LLM は自分で決める。判断役は route() で後から決める
    chart_id: Optional[str] = None
    args: Dict[str, str] = field(default_factory=dict)
    highlight: Optional[str] = None
    candidates: List[str] = field(default_factory=list)  # 聞き返しの候補
    # ---- 判断役のみ
    answerable: Optional[float] = None
    chart_conf: Optional[float] = None
    arg_confs: Dict[str, float] = field(default_factory=dict)
    highlight_conf: Optional[float] = None
    chart_probs: Dict[str, float] = field(default_factory=dict)
    # ---- 検証
    invalid: Optional[str] = None  # カタログに収まらない出力だったときの理由
    refused: bool = False  # 判断役・LLM が拒否の応答を返した


def assemble_judge_prediction(answers: Dict[str, NormAnswer]) -> Prediction:
    """判断役の全回答から、選ばれたチャートに必要な分だけを拾って Prediction にする。"""
    pred = Prediction()
    if any(a.kind == "refusal" for a in answers.values()):
        pred.refused = True
        return pred

    pred.answerable = answers[ANSWERABLE].probability
    chart = answers[CHART]
    pred.chart_id = chart.choice
    pred.chart_conf = chart.confidence
    pred.chart_probs = chart.probabilities
    hl = answers[HIGHLIGHT]
    pred.highlight = hl.choice
    pred.highlight_conf = hl.confidence

    if pred.chart_id in CATALOG:
        for arg in CATALOG[pred.chart_id].args:
            a = answers[arg_question_name(pred.chart_id, arg.name)]
            pred.args[arg.name] = a.choice
            pred.arg_confs[arg.name] = a.confidence
        pred.invalid = validate_request(pred.chart_id, pred.args)
    elif pred.chart_id != NONE_OF_THESE:
        pred.invalid = f"未知の chart_id: {pred.chart_id!r}"
    return pred


def top_chart_candidates(pred: Prediction, n: int = 3) -> List[str]:
    """聞き返しで見せる候補。確率の高い順に、「どれも当てはまらない」を除いて n 件。"""
    ranked = sorted(pred.chart_probs.items(), key=lambda kv: kv[1], reverse=True)
    return [cid for cid, _ in ranked if cid in CATALOG][:n]


def route(
    pred: Prediction,
    t_reject: float = 0.2,
    t_llm: float = 0.5,
    t_run: float = 0.8,
    include_highlight: bool = True,
) -> str:
    """設計書 7 章の振り分け。"reject" / "fallback"（LLM へ）/ "ask_back" / "run" を返す。"""
    if pred.refused:
        return "fallback"
    if pred.answerable < t_reject:
        return "reject"
    if pred.chart_id == NONE_OF_THESE or pred.invalid:
        return "fallback"
    confs = [pred.chart_conf, *pred.arg_confs.values()]
    if include_highlight:
        confs.append(pred.highlight_conf)
    weakest = min(confs)
    if weakest < t_llm or pred.answerable < t_llm:
        return "fallback"
    if weakest < t_run:
        return "ask_back"
    return "run"


def judge_to_final(pred: Prediction, **route_kwargs: Any) -> Prediction:
    """判断役だけで完結する場合の最終的な答え（fallback になったものは action="fallback" のまま）。"""
    action = route(pred, **route_kwargs)
    final = Prediction(action=action, answerable=pred.answerable, invalid=pred.invalid)
    if action == "run":
        final.chart_id, final.args, final.highlight = pred.chart_id, dict(pred.args), pred.highlight
    elif action == "ask_back":
        final.candidates = top_chart_candidates(pred)
    return final


# ---------------------------------------------------------------- LLM のツール定義

ASK_BACK_TOOL = "ask_back"
REJECT_TOOL = "reject"

LLM_SYSTEM_PROMPT = (
    "あなたは飲食店の売上分析アプリのアシスタントです。ユーザーの質問に合うグラフを、"
    "用意されたツールの中から1つ選んで呼び出してください。\n"
    "- グラフのツールは、そのグラフと引数を指定して表示する。質問で指定されていない引数は、"
    "各引数の説明にある既定値を使う\n"
    "- 期間（先月・去年の夏など）は別の処理が解釈するので、考えなくてよい\n"
    "- 質問が曖昧で、どのグラフか決められないときは ask_back を呼び、候補のグラフを挙げる\n"
    "- このデータで答えられない質問（天気、将来の予測、従業員、原価、競合店など）は reject を呼ぶ\n"
    "- 直前の指定がある場合、「じゃあ夜は？」のような省略は直前のグラフと引数を引き継ぐ"
)


def build_user_message(question: str, previous_request: Optional[dict]) -> str:
    msg = f"質問: {question}"
    if previous_request:
        msg += "\n直前の指定: " + json.dumps(previous_request, ensure_ascii=False)
    return msg


def _options_text(options: Dict[str, str]) -> str:
    return " / ".join(f"{v}={d}" for v, d in options.items())


def build_tools() -> List[Dict[str, Any]]:
    """カタログのツール定義（Anthropic 形式）。他社の形式にもこの dict から変換できる。"""
    tools: List[Dict[str, Any]] = []
    highlight_schema = {
        "type": "string",
        "enum": list(HIGHLIGHTS),
        "description": "目立たせたい点の種類。" + _options_text(HIGHLIGHTS) + "。指定がなければ none",
    }
    for chart in CHARTS:
        props: Dict[str, Any] = {}
        for arg in chart.args:
            props[arg.name] = {
                "type": "string",
                "enum": list(arg.options),
                "description": f"{arg.description}。{_options_text(arg.options)}。既定値は{arg.default}",
            }
        props["highlight"] = highlight_schema
        tools.append(
            {
                "name": chart.id,
                "description": chart.description,
                "strict": True,
                "input_schema": {
                    "type": "object",
                    "properties": props,
                    "required": list(props),
                    "additionalProperties": False,
                },
            }
        )
    tools.append(
        {
            "name": ASK_BACK_TOOL,
            "description": "質問が曖昧で、どのグラフか決められないとき、候補のグラフを挙げて聞き返す",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "candidates": {
                        "type": "array",
                        "items": {"type": "string", "enum": [c.id for c in CHARTS]},
                        "description": "候補のグラフ（可能性の高い順）",
                    }
                },
                "required": ["candidates"],
                "additionalProperties": False,
            },
        }
    )
    tools.append(
        {
            "name": REJECT_TOOL,
            "description": "このデータでは答えられない質問のとき、対応外として返す",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {"reason": {"type": "string", "description": "答えられない理由（短く）"}},
                "required": ["reason"],
                "additionalProperties": False,
            },
        }
    )
    return tools


def parse_tool_call(name: str, tool_input: Dict[str, Any]) -> Prediction:
    """LLM のツール呼び出しを Prediction にする。カタログに収まらなければ invalid に理由を入れる。"""
    if name == REJECT_TOOL:
        return Prediction(action="reject")
    if name == ASK_BACK_TOOL:
        cands = [c for c in tool_input.get("candidates", []) if c in CATALOG]
        return Prediction(action="ask_back", candidates=cands)
    if name not in CATALOG:
        return Prediction(action="run", chart_id=name, invalid=f"未知のツール: {name!r}")
    args = {k: v for k, v in tool_input.items() if k != "highlight"}
    pred = Prediction(action="run", chart_id=name, args=args, highlight=tool_input.get("highlight"))
    pred.invalid = validate_request(name, args)
    if pred.highlight not in HIGHLIGHTS:
        pred.invalid = pred.invalid or f"highlight が範囲外: {pred.highlight!r}"
    return pred


# ---------------------------------------------------------------- 保存した応答から Prediction を作り直す


def prediction_from_raw(kind: str, raw: Dict[str, Any]) -> Prediction:
    """保存した生の応答（run.py の `raw`）から Prediction を作る。しきい値は後から route() で変えられる。"""
    if kind == "jev":
        return assemble_judge_prediction(parse_jev_response(raw))
    if kind == "decisions":
        return assemble_judge_prediction(parse_decisions_response(raw))
    if kind in ("claude", "openai"):
        if raw.get("stop_reason") == "refusal":
            return Prediction(refused=True)
        if not raw.get("tool"):
            return Prediction(invalid="ツールが呼ばれなかった")
        return parse_tool_call(raw["tool"], raw["input"] or {})
    raise ValueError(f"unknown kind: {kind}")
