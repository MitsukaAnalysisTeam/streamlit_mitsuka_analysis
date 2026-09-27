from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap
from src.components.utils.menu_analysis.s2_classification.TransactionAggregator import pivot_by_category, variety
from src.components.utils.menu_analysis.s2_classification.TransactionCategoryMap import TransactionCategoryMap
from src.components.utils.menu_analysis.s1_data_sources.LoaderAfter202606 import LoaderAfter202606


class AlcoholTransactionUtils:
    """会計別データから、アルコールの味カテゴリを集計するクラス（時間帯フィルタなし）。

    アルコール系カテゴリの一覧は`menu.json`のflag(alcohol)から取得する。
    「ちょい飲み・酔いどれ」（おかわり系）はflag未設定のため今回のスコープ外のまま対象外。
    """

    def __init__(
        self,
        loader: LoaderAfter202606 = None,
        category_map: TransactionCategoryMap = None,
        category_unify_map: CategoryUnifyMap = None,
    ):
        self._loader = loader or LoaderAfter202606()
        self._category_map = category_map or TransactionCategoryMap()
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def get_alcohol_dict(self, mode: str = "販売数") -> dict:
        df = self._loader.get_transactions()
        if df.empty:
            return {}

        df = df.copy()
        df["味カテゴリ"] = df.apply(
            lambda r: self._category_map.get_category(r["メニュー名"], variety(r)),
            axis=1,
        )
        target = df[df["味カテゴリ"].apply(
            lambda c: "4" in self._category_unify_map.flags(c)
        )]

        value_col = "注文数量" if mode == "販売数" else "明細金額"
        return pivot_by_category(target, value_col)
