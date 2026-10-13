import pandas as pd

OTHER_LABEL = "その他"

LEGEND_HINT_TEXT = "👇凡例をクリックすると、そのカテゴリの表示/非表示を切り替えられます。"


def legend_hint_annotation(y: float = -0.12) -> dict:
    """円グラフ本体と凡例の間に置く、ヒント用のPlotly注釈(annotation)を返す。

    Plotlyのannotationは角丸に対応していないため、背景色付きの四角い
    ラベルになる。yはpaper座標（円グラフ本体がおおよそ0〜1、凡例が
    それより下のマイナス側）で、呼び出し側のlegendのy位置と噛み合うよう
    に調整すること。
    """
    return dict(
        text=LEGEND_HINT_TEXT,
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0.5,
        y=y,
        xanchor="center",
        yanchor="middle",
        bgcolor="#e8e8e8",
        borderpad=6,
        font=dict(size=11, color="#444444"),
        align="center",
    )


def group_minor_slices(
    totals: pd.Series,
    threshold: float = 0.03,
    other_label: str = OTHER_LABEL,
) -> pd.Series:
    """全体に占める割合がthreshold未満の項目を1つのother_labelにまとめて返す。

    円グラフの隣接スライスが増えすぎて色が判別しにくくなる・凡例が
    埋まりすぎるのを防ぐために使う。まとめられる項目が無ければtotalsを
    そのまま返す。major項目の並び順はtotals通りを維持し、other_labelは
    常に末尾に追加する。
    """
    total_sum = totals.sum()
    if total_sum <= 0:
        return totals

    is_major = (totals / total_sum) >= threshold
    if is_major.all():
        return totals

    major = totals[is_major]
    other_sum = totals[~is_major].sum()
    return pd.concat([major, pd.Series({other_label: other_sum})])


def other_slice_legend_label(
    totals: pd.Series,
    threshold: float = 0.03,
    other_label: str = OTHER_LABEL,
    max_names: int = 5,
) -> str:
    """「その他」に何がまとめられたかを凡例に出すための文字列を返す。

    例: "その他（つけ麺8号、担々麺、酒粕ラーメン 他3件）"
    まとめられる項目が無ければ空文字を返す。totalsはgroup_minor_slices適用前
    （グループ化していない生のSeries）を渡すこと。
    """
    total_sum = totals.sum()
    if total_sum <= 0:
        return ""

    is_major = (totals / total_sum) >= threshold
    minor_labels = totals[~is_major].index.tolist()
    if not minor_labels:
        return ""

    if len(minor_labels) <= max_names:
        detail = "、".join(minor_labels)
    else:
        shown = "、".join(minor_labels[:max_names])
        rest = len(minor_labels) - max_names
        detail = f"{shown} 他{rest}件"

    return f"{other_label}（{detail}）"
