"""フォールバック LLM（Claude Haiku 5.5）のアダプタ。カタログをツール定義として渡し、ツールコーリングで答えさせる。"""
from __future__ import annotations

from typing import Any, Dict, Optional

import common as c


class ClaudeAdapter:
    kind = "claude"
    key_env = "ANTHROPIC_API_KEY"

    def __init__(self, model: str = "claude-haiku-5-5", client: Any = None, effort: str = "low", max_tokens: int = 2048):
        self.model = model
        self._client = client
        self.effort = effort
        self.max_tokens = max_tokens
        self._tools = c.build_tools()

    def _get_client(self):
        if self._client is None:
            import anthropic  # 遅延 import（dry-run・テストでは不要）

            self._client = anthropic.Anthropic(api_key=c.require_key(self.key_env), max_retries=3)
        return self._client

    def build_request(self, row: Dict[str, Any], with_none: bool = False, seed: Optional[int] = None) -> Dict[str, Any]:
        # temperature は指定しない（Haiku 5.5 は 1 以外で 400）。再現性はツール引数の enum で担保する。
        # 必ずツールを呼ばせる（ask_back / reject も用意してある）。思考は effort で最小にする。
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": c.LLM_SYSTEM_PROMPT,
            "tools": self._tools,
            "tool_choice": {"type": "any"},
            "output_config": {"effort": self.effort},
            "messages": [{"role": "user", "content": c.build_user_message(row["question"], row["previous_request"])}],
        }

    def call(self, row: Dict[str, Any], with_none: bool = False, seed: Optional[int] = None) -> Dict[str, Any]:
        resp = self._get_client().messages.create(**self.build_request(row))
        # 先頭が思考ブロックのことがあるので、content[0] ではなく type で探す
        tool = next((b for b in resp.content if b.type == "tool_use"), None)
        u = resp.usage
        return {
            "raw": {
                "tool": tool.name if tool else None,
                "input": dict(tool.input) if tool else None,
                "stop_reason": resp.stop_reason,
            },
            "usage": {
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", None),
                "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", None),
            },
        }
