from src.components.utils.menu_analysis.s3_transaction.AlcoholTransactionUtils import AlcoholTransactionUtils
from src.components.utils.menu_analysis.s2_classification.CategoryUnifyMap import CategoryUnifyMap
from src.components.utils.menu_analysis.s3_transaction.FacadeMergeUtils import (
    filter_before_cutover,
    filter_on_or_after_cutover,
    merge_dicts,
)
from src.components.utils.menu_analysis.s3_transaction.RamenTransactionUtils import RamenTransactionUtils

# ランチ分析ページ固有の表示ラベル調整（新旧カテゴリ名の統一自体はmenu.jsonが担う）
_LUNCH_OTHER_CATEGORY_RENAME = {
    "発酵御膳": "発酵御膳",
    "キッズ": "キッズ",
    "唐揚げ定食": "発酵唐揚げプレート",
}
_LUNCH_SET_SOURCE_CATEGORY = "昼セット"
_LUNCH_SET_TARGET_CATEGORY = "セット"


def _merge_legacy_and_new(
    get_by_product_df,
    df_val,
    legacy_json: dict,
    new_dict: dict,
    legacy_transform=None,
) -> dict:
    """旧スプレッドシートデータ(cutover前)と新会計別データ(cutover以降)を
    カテゴリ別df_dictの形でマージする共通処理。

    3つのFacade（Ramen/Lunch/Alcohol）で全く同じ手順（旧データ取得→cutoverで
    前後に分割→必要ならカテゴリ正規化→新データをcutoverで分割→日付軸でマージ）
    になるため、ここに集約している。
    """
    legacy_dict = get_by_product_df.json_to_df_dict(df_all=df_val, json_dict=legacy_json)
    legacy_dict = filter_before_cutover(legacy_dict)
    if legacy_transform:
        legacy_dict = legacy_transform(legacy_dict)

    new_dict = filter_on_or_after_cutover(new_dict)

    return merge_dicts(legacy_dict, new_dict)


class RamenAnalysisFacade:
    """ラーメン全体分析（昼/夜/深夜比較）向けに、旧スプレッドシートデータと
    新会計別データ(2026-06-01〜)をカテゴリ別df_dictの形でマージするFacade。
    """

    def __init__(
        self,
        get_by_product_df,
        lunch_json: dict,
        diner_json: dict,
        midnight_json: dict,
        ramen_transaction_utils: RamenTransactionUtils = None,
        category_unify_map: CategoryUnifyMap = None,
    ):
        self._get_by_product_df = get_by_product_df
        self._legacy_json_by_slot = {
            "昼": lunch_json,
            "夜": diner_json,
            "深夜": midnight_json,
        }
        self._ramen_transaction_utils = ramen_transaction_utils or RamenTransactionUtils()
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def get_slot_dict(self, slot: str, mode: str) -> dict:
        df_val = (
            self._get_by_product_df.df_all_sale
            if mode == "売上"
            else self._get_by_product_df.df_all_num
        )
        new_dict = self._ramen_transaction_utils.get_slot_dict(slot, mode)
        return _merge_legacy_and_new(
            self._get_by_product_df,
            df_val,
            self._legacy_json_by_slot[slot],
            new_dict,
            # 旧データ側のカテゴリ名も新データ側と同じ統一名に正規化してからマージする
            # （新データ側にしかリネームが適用されていなかった非対称を解消）
            legacy_transform=self._category_unify_map.normalize,
        )


class LunchAnalysisFacade:
    """ランチ分析（昼カテゴリ別+セット内訳）向けに、旧スプレッドシートデータと
    新会計別データ(2026-06-01〜)をカテゴリ別df_dictの形でマージするFacade。
    """

    def __init__(
        self,
        get_by_product_df,
        lunch_json: dict,
        ramen_transaction_utils: RamenTransactionUtils = None,
        category_unify_map: CategoryUnifyMap = None,
    ):
        self._get_by_product_df = get_by_product_df
        self._lunch_json = lunch_json
        self._ramen_transaction_utils = ramen_transaction_utils or RamenTransactionUtils()
        self._category_unify_map = category_unify_map or CategoryUnifyMap()

    def get_lunch_dict(self, mode: str) -> dict:
        df_val = (
            self._get_by_product_df.df_all_sale
            if mode == "売上"
            else self._get_by_product_df.df_all_num
        )
        new_dict = self._scope_to_lunch_page(self._ramen_transaction_utils.get_slot_dict("昼", mode))
        return _merge_legacy_and_new(
            self._get_by_product_df,
            df_val,
            self._lunch_json,
            new_dict,
            # 旧データ側(legacy_json由来)にも同じ絞り込み・リネームを適用してからマージする
            # （新データ側にしか適用されておらず、旧データ側の'昼セット'が'セット'に
            # リネームされないままマージされ、新旧が別カテゴリとして分裂していた非対称を解消）
            legacy_transform=self._scope_to_lunch_page,
        )

    def _scope_to_lunch_page(self, base: dict) -> dict:
        """味カテゴリ別dictから、ランチ分析ページ向けに絞り込み・リネームする。
        新データ・旧データ(legacy_json由来)の両方に同じ変換を適用する。

        - ラーメン系: そのまま
        - セット系: '昼セット'のみを'セット'にリネーム（'夜セット'は対象外）
        - その他: 発酵御膳/キッズ/唐揚げ定食（→発酵唐揚げプレートにリネーム）
        """
        result = {
            category: df
            for category, df in base.items()
            if self._category_unify_map.is_ramen(category)
        }

        if _LUNCH_SET_SOURCE_CATEGORY in base:
            result[_LUNCH_SET_TARGET_CATEGORY] = base[_LUNCH_SET_SOURCE_CATEGORY]

        for source_key, target_key in _LUNCH_OTHER_CATEGORY_RENAME.items():
            if source_key in base:
                result[target_key] = base[source_key]

        return result


class AlcoholAnalysisFacade:
    """アルコール分析向けに、旧スプレッドシートデータと
    新会計別データ(2026-06-01〜)をカテゴリ別df_dictの形でマージするFacade。
    時間帯フィルタは行わない（終日対象）。
    """

    def __init__(
        self,
        get_by_product_df,
        alcohol_json: dict,
        alcohol_transaction_utils: AlcoholTransactionUtils = None,
    ):
        self._get_by_product_df = get_by_product_df
        self._alcohol_json = alcohol_json
        self._alcohol_transaction_utils = alcohol_transaction_utils or AlcoholTransactionUtils()

    def get_alcohol_dict(self, mode: str) -> dict:
        df_val = (
            self._get_by_product_df.df_all_num
            if mode == "平均杯数"
            else self._get_by_product_df.df_all_sale
        )
        transaction_mode = "販売数" if mode == "平均杯数" else "売上"
        new_dict = self._alcohol_transaction_utils.get_alcohol_dict(transaction_mode)
        return _merge_legacy_and_new(self._get_by_product_df, df_val, self._alcohol_json, new_dict)
