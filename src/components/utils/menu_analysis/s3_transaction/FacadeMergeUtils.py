import datetime

import pandas as pd

from src.components.utils.menu_analysis.s2_classification.TransactionAggregator import sum_duplicate_columns

CUTOVER_DATE = datetime.date(2026, 6, 1)


def _to_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df.index = pd.to_datetime(df.index)
    return df


def filter_before_cutover(df_dict: dict) -> dict:
    result = {}
    for key, df in df_dict.items():
        df = _to_datetime_index(df)
        result[key] = df[df.index < pd.Timestamp(CUTOVER_DATE)] if not df.empty else df
    return result


def filter_on_or_after_cutover(df_dict: dict) -> dict:
    result = {}
    for key, df in df_dict.items():
        df = _to_datetime_index(df)
        result[key] = df[df.index >= pd.Timestamp(CUTOVER_DATE)] if not df.empty else df
    return result


def merge_dicts(legacy: dict, new: dict) -> dict:
    """新旧2つの{カテゴリ名: DataFrame(index=日付, columns=商品名)}を、
    日付軸で結合してカテゴリごとに1つのDataFrameにまとめる。
    """
    merged = {}
    for key in set(legacy) | set(new):
        frames = [df for df in (legacy.get(key), new.get(key)) if df is not None and not df.empty]
        if not frames:
            merged[key] = pd.DataFrame()
            continue
        # 列名重複（旧JSONの二重登録等）があるとpd.concatが失敗するため、結合前に列を統一する
        frames = [sum_duplicate_columns(df) for df in frames]
        combined = pd.concat(frames)
        result_df = combined.groupby(combined.index).sum().fillna(0)
        # legacy(索引名"日付")と新データ(索引名"会計日")の結合でindex.nameがNoneになるため、
        # 既存コード(AlcoholAnalysisUtils等)が前提とする"日付"に統一する。
        result_df.index.name = "日付"
        merged[key] = result_df
    return merged
