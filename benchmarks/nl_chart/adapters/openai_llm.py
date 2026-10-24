"""フォールバック LLM（GPT-6 Luna）のアダプタ。Responses API の関数呼び出しで答えさせる。

Chat Completions の関数呼び出しは `reasoning_effort` が none のときしか使えないため、Responses API を使う。
Decisions API（判断役）と同じ `OPENAI_API_KEY` で動く。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import common as c
from adapters.http_judges import Post, http_post

RESPONSES_URL = "https://api.openai.com/v1/responses"


def to_responses_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Anthropic 形式のツール定義（common.build_tools）を Responses API の形式にする。"""
    return [
        {
            "type": "function",
            "name": t["name"],
            "description": t["description"],
            "parameters": t["input_schema"],
            "strict": True,
        }
        for t in tools
    ]


class OpenAILLMAdapter:
    kind = "openai"
    key_env = "OPENAI_API_KEY"

    def __init__(self, model: str = "gpt-6-luna", effort: str = "low", max_output_tokens: int = 2048,
                 post: Optional[Post] = None, api_key: Optional[str] = None):
        self.model = model
        self.effort = effort
        self.max_output_tokens = max_output_tokens
        self._post = post or http_post
        self._api_key = api_key
        self._tools = to_responses_tools(c.build_tools())

    def build_request(self, row: Dict[str, Any], with_none: bool = False, seed: Optional[int] = None) -> Dict[str, Any]:
        # 必ず関数を呼ばせる（ask_back / reject も用意してある）。思考は effort で最小にする。
        return {
            "model": self.model,
            "instructions": c.LLM_SYSTEM_PROMPT,
            "input": c.build_user_message(row["question"], row["previous_request"]),
            "tools": self._tools,
            "tool_choice": "required",
            "parallel_tool_calls": False,
            "reasoning": {"effort": self.effort},
            "max_output_tokens": self.max_output_tokens,
        }

    def call(self, row: Dict[str, Any], with_none: bool = False, seed: Optional[int] = None) -> Dict[str, Any]:
        key = self._api_key or c.require_key(self.key_env)
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        resp = self._post(RESPONSES_URL, headers, self.build_request(row))
        output = resp.get("output", [])
        call = next((i for i in output if i.get("type") == "function_call"), None)
        refused = any(p.get("type") == "refusal" for i in output if i.get("type") == "message" for p in i.get("content", []))
        u = resp.get("usage") or {}
        return {
            "raw": {
                "tool": call["name"] if call else None,
                "input": json.loads(call["arguments"]) if call else None,
                "stop_reason": "refusal" if refused else resp.get("status"),
            },
            "usage": {
                "input_tokens": u.get("input_tokens"),
                "output_tokens": u.get("output_tokens"),
                "cached_tokens": (u.get("input_tokens_details") or {}).get("cached_tokens"),
                "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens"),
            },
        }
