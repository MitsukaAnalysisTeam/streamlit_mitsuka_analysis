import pandas as pd


def variety(row) -> str:
    """会計別データの「種別１」からバリエーション文字列を取り出す。

    バリエーションが無い商品は本来空欄のはずだが、実データでは
    文字列の"0"が入っている（menu.json側に"(0)"という表記は存在しない
    ため、"0"は常に「バリエーション無し」を意味すると判断できる）。
    """
    v = row["種別１"]
    if pd.isna(v) or v == "0":
        return ""
    return v


def item_label(row) -> str:
    v = variety(row)
    return row["メニュー名"] if v == "" else f"{row['メニュー名']}({v})"


def sum_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """同名列が複数ある場合、列名ごとに合算した1列にまとめる。"""
    if df.empty:
        return df
    result = {}
    for col in df.columns.unique():
        sub = df[col]
        result[col] = sub.sum(axis=1) if isinstance(sub, pd.DataFrame) else sub
    return pd.DataFrame(result)


def pivot_by_category(
    df: pd.DataFrame, value_col: str, category_col: str = "味カテゴリ"
) -> dict:
    """味カテゴリ列でグループ化し、{カテゴリ名: DataFrame(index=会計日, columns=商品ラベル)}を返す。"""
    if df.empty:
        return {}
    df = df.copy()
    df["商品ラベル"] = df.apply(item_label, axis=1)
    result = {}
    for category, group in df.groupby(category_col):
        pivot = group.pivot_table(
            index="会計日",
            columns="商品ラベル",
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
        pivot.index = pd.to_datetime(pivot.index)
        result[category] = pivot
    return result
