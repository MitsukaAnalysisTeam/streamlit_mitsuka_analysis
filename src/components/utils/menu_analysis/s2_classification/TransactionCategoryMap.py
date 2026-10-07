import json
import re

from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import UNCATEGORIZED


class TransactionCategoryMap:
    _PATTERN = re.compile(r"^(.+?)\((.*)\)$")

    def __init__(self, json_path: str = "data/json/menu.json"):
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)
        # (メニュー名, 種別1) -> カテゴリ の逆引き辞書を構築
        self._map = {}
        for category, config in raw.items():
            for item in config.get("item", []):
                key = self._parse(item)
                # 重複キーは最初の登録を優先（キッズ等の意図的重複に注意）
                self._map.setdefault(key, category)

    def _parse(self, item: str) -> tuple:
        m = self._PATTERN.match(item)
        if m:
            return (m.group(1).strip(), m.group(2).strip())
        return (item.strip(), "")

    def _normalize(self, s: str) -> str:
        return s.replace("?", "〜").strip() if isinstance(s, str) else ""

    def get_category(self, menu_name: str, variety: str) -> str:
        key = (self._normalize(menu_name), self._normalize(variety))
        return self._map.get(key, UNCATEGORIZED)
