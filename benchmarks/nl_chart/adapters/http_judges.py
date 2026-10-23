"""判断役（Jev / OpenAI Decisions API）のアダプタ。

どちらも「質問を1リクエストにまとめて送り、確率つきの回答を受け取る」形式。
`post` は差し替え可能（単体テストでは偽の応答を返す）。
"""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, Optional, Tuple

import common as c

Post = Callable[[str, Dict[str, str], Dict[str, Any]], Dict[str, Any]]

JEV_URL = "https://api.typesafe.ai/v1/systemone"
DECISIONS_URL = "https://api.openai.com/v1/decisions"

_RETRY_STATUS = {429, 500, 502, 503, 504}


def http_post(url: str, headers: Dict[str, str], body: Dict[str, Any], retries: int = 3, timeout: int = 60) -> Dict[str, Any]:
    import requests

    for attempt in range(retries + 1):
        try:
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        except requests.RequestException:
            if attempt == retries:
                raise
        else:
            if resp.status_code not in _RETRY_STATUS:
                resp.raise_for_status()  # 4xx（422 の detail など）はそのまま例外にする
                return resp.json()
            if attempt == retries:
                resp.raise_for_status()
        time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


class _JudgeAdapter:
    kind = ""  # "jev" | "decisions"
    url = ""
    key_env = ""

    def __init__(self, model: str, post: Optional[Post] = None, api_key: Optional[str] = None):
        self.model = model
        self._post = post or http_post
        self._api_key = api_key
        self._questions: Dict[Tuple[bool, Optional[int]], Any] = {}

    def _headers(self) -> Dict[str, str]:
        key = self._api_key or c.require_key(self.key_env)
        return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def questions(self, with_none: bool, seed: Optional[int]):
        k = (with_none, seed)
        if k not in self._questions:
            self._questions[k] = c.build_questions(with_none=with_none, seed=seed)
        return self._questions[k]

    def build_request(self, row: Dict[str, Any], with_none: bool, seed: Optional[int]) -> Dict[str, Any]:
        raise NotImplementedError

    def call(self, row: Dict[str, Any], with_none: bool, seed: Optional[int]) -> Dict[str, Any]:
        """生の応答（`raw`）と使用量を返す。"""
        body = self.build_request(row, with_none, seed)
        resp = self._post(self.url, self._headers(), body)
        return {"raw": resp, "usage": self.usage(resp)}

    def usage(self, resp: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class JevAdapter(_JudgeAdapter):
    kind = "jev"
    url = JEV_URL
    key_env = "TYPESAFE_API_KEY"

    def build_request(self, row, with_none, seed):
        state = c.build_state(row["question"], row["previous_request"])
        return c.to_jev_request(self.model, state, self.questions(with_none, seed))

    def usage(self, resp):
        u = resp.get("usage", {})
        return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}


class DecisionsAdapter(_JudgeAdapter):
    kind = "decisions"
    url = DECISIONS_URL
    key_env = "OPENAI_API_KEY"

    def build_request(self, row, with_none, seed):
        state = c.build_state(row["question"], row["previous_request"])
        return c.to_decisions_request(self.model, state, self.questions(with_none, seed))

    def usage(self, resp):
        u = resp.get("usage") or {}
        return {"input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens")}
