from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap
from src.components.utils.menu_analysis.s2_classification.TransactionAggregator import pivot_by_category, variety
from src.components.utils.menu_analysis.s2_classification.TransactionCategoryMap import TransactionCategoryMap
from src.components.utils.menu_analysis.s1_data_sources.LoaderAfter202606 import LoaderAfter202606
import src.components.utils.menu_analysis.s2_classification.TimeSlotClassifier as TimeSlotClassifier


class RamenTransactionUtils:
    """会計別データから、ラーメンの味カテゴリを昼/夜/深夜ごとに集計するクラス。

    新旧カットオーバーでの表記ゆれ・分類は`menu.json`(`CategoryUnifyMap`)に
    集約しており、ここでは会計データの時間帯フィルタとピボットのみを行う。
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

    def get_slot_dict(self, slot: str, mode: str = "販売数") -> dict:
        """slot: '昼' | '夜' | '深夜'、mode: '販売数' | '売上'

        # TODO: 要確認 - 'サンセット'(14:30-17:30)の注文はこの3区分のどこにも
        # 含めていない。既存の ramen_analysis() 自体が昼/夜/深夜の3区分のみ対応で
        # サンセット枠を持たないため、旧システムと同様の扱いとしている。
        """
        df = self._loader.get_transactions()
        if df.empty:
            return {}

        df = df.copy()
        df["味カテゴリ"] = df.apply(
            lambda r: self._category_map.get_category(r["メニュー名"], variety(r)),
            axis=1,
        )
        df["時間帯"] = df.apply(
            lambda r: TimeSlotClassifier.classify(r["会計時間"], r["曜日"]), axis=1
        )

        target = df[df["時間帯"] == slot]
        if slot == "昼":
            target = target[target["曜日"].apply(TimeSlotClassifier.is_lunch_weekday)]

        value_col = "注文数量" if mode == "販売数" else "明細金額"
        result = pivot_by_category(target, value_col)

        return self._category_unify_map.normalize(result)
