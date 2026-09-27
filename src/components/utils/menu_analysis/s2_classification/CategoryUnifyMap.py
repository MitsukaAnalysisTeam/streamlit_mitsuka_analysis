import json

import pandas as pd

from src.components.utils.menu_analysis.s2_classification.TransactionAggregator import sum_duplicate_columns

# flagコードの意味。新しい分析軸を追加する時だけ変わる、滅多に更新されない定義のため
# JSON側には持たせずここで固定する。
FLAG_LEGEND = {
    "1": "ramen",
    "2": "set",
    "3": "other_food",
    "4": "alcohol",
    "4.1": "beer",   # alcohol配下のサブ分類。親(4)と併記する（例: ["4", "4.1"]）
    "4.2": "sake",   # 秋鹿系
    "4.3": "wine",
}

UNCATEGORIZED = "未分類"


class CategoryUnifyMap:
    """カテゴリ別df_dictのキーに分類flagを付与し、統一カテゴリ名に正規化するクラス。

    `menu.json`（{統一カテゴリ名: {"flag": [...], "item": [...]}}）を読み込む。
    `item`一覧は新旧すべてのデータソースの生商品名を統一カテゴリ名ごとに束ねた
    マスタで、表記ゆれ・割り当てミスは事前に解消済み（旧`menu.json`（フラットな
    配列形式）/`lunch.json`/`ディナー.json`/`深夜限定.json`/`alcohol.json`/
    `category_rename.json`の後継。ファイル名は同じだが中身は別物）。
    `TransactionCategoryMap`が既にこのマスタでカテゴリ名を確定させているため、
    ここでの`canonical_name()`は実質的に恒等写像になるが、`flags()`/`is_ramen()`
    による分類flag参照のために引き続き利用する。
    """

    def __init__(self, json_path: str = "data/json/menu.json"):
        with open(json_path, encoding="utf-8") as f:
            raw = json.load(f)

        self._flags = {}
        self._items = {}
        self._alias_to_canonical = {}
        for canonical, config in raw.items():
            self._flags[canonical] = set(config.get("flag", []))
            self._items[canonical] = config.get("item", [])
            self._alias_to_canonical[canonical] = canonical
            for alias in config.get("item", []):
                self._alias_to_canonical.setdefault(alias, canonical)

    def canonical_name(self, raw_category: str) -> str:
        return self._alias_to_canonical.get(raw_category, UNCATEGORIZED)

    def flags(self, category: str) -> set:
        return self._flags.get(category, set())

    def is_ramen(self, category: str) -> bool:
        return "1" in self.flags(category)

    def items_by_flag(self, flag: str) -> dict:
        """指定flagを持つカテゴリを{統一カテゴリ名: [生商品名, ...]}の形で返す。

        `json_to_df_dict`（`LoaderBefore202606.py`）に渡す、カテゴリごとの列名リストを
        組み立てる用途。alcohol_json等の旧フラット形式JSONの代替として使う。
        """
        return {
            canonical: items
            for canonical, items in self._items.items()
            if flag in self._flags.get(canonical, set())
        }

    def normalize(self, df_dict: dict) -> dict:
        """{生カテゴリ名: DataFrame}を{統一カテゴリ名: DataFrame}に正規化する。

        複数の表記ゆれ（例: 新データの'あっさりエビ味噌'と旧データの'海老みそ'）が
        同じ統一カテゴリ名に畳み込まれる場合は、列を合算する。
        """
        grouped = {}
        for raw_category, df in df_dict.items():
            canonical = self.canonical_name(raw_category)
            grouped.setdefault(canonical, []).append(df)

        result = {}
        for canonical, frames in grouped.items():
            if len(frames) == 1:
                result[canonical] = frames[0]
            else:
                combined = pd.concat(frames, axis=1).fillna(0)
                result[canonical] = sum_duplicate_columns(combined)
        return result
