"""描画済みの Plotly の図に、強調（最大・最小・最も変化した点）を重ねる。

強調する点はコードが数値から決める。判断役が選ぶのは種類だけ（catalog.HIGHLIGHTS）。
既存のグラフ関数は図を作って st.plotly_chart に渡すだけなので、`intercept` でその直前に横取りして書き足す。
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import List, Optional

import plotly.graph_objects as go
import streamlit as st

_COLOR = "#d62728"


def _fmt(v: float) -> str:
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:,.1f}"


def _bar_series(fig: go.Figure):
    """棒グラフの x と、比べるための値（積み上げは合計、2系列の並びは差）を返す。"""
    bars = [t for t in fig.data if t.type == "bar" and t.y is not None]
    if not bars:
        return None
    xs = list(bars[0].x)
    ys = [[(v if v is not None else 0) for v in b.y] for b in bars]
    totals = [sum(col) for col in zip(*ys)]
    return xs, ys, totals


def _pick(kind: str, xs: list, ys: list, totals: List[float]) -> Optional[tuple]:
    """(位置, 強調の説明) を返す。"""
    if not totals:
        return None
    if kind == "max":
        i = max(range(len(totals)), key=totals.__getitem__)
        return i, f"最大: {xs[i]}（{_fmt(totals[i])}）"
    if kind == "min":
        i = min(range(len(totals)), key=totals.__getitem__)
        return i, f"最小: {xs[i]}（{_fmt(totals[i])}）"
    if kind == "biggest_change":
        if len(ys) == 2:  # 2つの月を並べた図は、同じ位置どうしの差
            diffs = [b - a for a, b in zip(ys[0], ys[1])]
            i = max(range(len(diffs)), key=lambda k: abs(diffs[k]))
            return i, f"最も変化: {xs[i]}（{diffs[i]:+,.0f}）"
        if len(totals) < 2:
            return None
        diffs = [totals[k] - totals[k - 1] for k in range(1, len(totals))]
        j = max(range(len(diffs)), key=lambda k: abs(diffs[k]))
        return j + 1, f"最も変化: {xs[j]}→{xs[j + 1]}（{diffs[j]:+,.0f}）"
    return None


def apply_highlight(fig: go.Figure, kind: str) -> Optional[str]:
    """図に強調を書き足す。何を強調したかの説明を返す（強調しなかったら None）。"""
    if kind in (None, "none"):
        return None

    pies = [t for t in fig.data if t.type == "pie"]
    if pies:
        notes = []
        for pie in pies:
            vals = list(pie.values)
            if kind not in ("max", "min") or not vals:
                continue
            i = max(range(len(vals)), key=vals.__getitem__) if kind == "max" else min(range(len(vals)), key=vals.__getitem__)
            pie.pull = [0.15 if k == i else 0 for k in range(len(vals))]
            total = sum(vals) or 1
            notes.append(f"{'最大' if kind == 'max' else '最小'}: {pie.labels[i]}（{vals[i] / total:.0%}）")
        return " / ".join(notes) or None

    series = _bar_series(fig)
    if not series:
        return None
    xs, ys, totals = series
    picked = _pick(kind, xs, ys, totals)
    if not picked:
        return None
    i, text = picked
    fig.add_annotation(
        x=xs[i], y=max(totals[i], max((col[i] for col in ys), default=0)), text=text.split("（")[0],
        showarrow=True, arrowhead=2, arrowcolor=_COLOR, ax=0, ay=-40, yshift=22,  # yshift: 棒の上の数値ラベルを避ける
        font=dict(color=_COLOR, size=13), bgcolor="white", bordercolor=_COLOR,
    )
    return text


@contextmanager
def intercept(kind: Optional[str], notes: List[str]):
    """この間に st.plotly_chart へ渡る図に強調を足し、説明を notes に集める。（デモ用。1 セッションずつの実行を前提）"""
    original = st.plotly_chart

    def patched(fig, *args, **kwargs):
        desc = apply_highlight(fig, kind)
        if desc:
            notes.append(desc)
        return original(fig, *args, **kwargs)

    st.plotly_chart = patched
    try:
        yield
    finally:
        st.plotly_chart = original
