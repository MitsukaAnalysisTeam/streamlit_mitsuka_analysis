"""質問文から期間（年月）を読み取る。判断役には期間を聞かず、コードで解釈する。

対応する表現: 「今月」「先月」「先々月」「2025年3月」「去年の夏」「今年」「3月から5月」「ここ3か月」「夏」など。
読み取れなければ None を返す（呼び出し側が、データのある最新月を使う）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Tuple

Month = Tuple[int, int]  # (年, 月)

_SEASONS = {"春": (3, 5), "夏": (6, 8), "秋": (9, 11), "冬": (12, 2)}
_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


@dataclass(frozen=True)
class Period:
    start: Month
    end: Month
    label: str  # 画面に出す「こう解釈した」の説明

    @property
    def is_single(self) -> bool:
        return self.start == self.end


def shift(ym: Month, months: int) -> Month:
    n = ym[0] * 12 + (ym[1] - 1) + months
    return n // 12, n % 12 + 1


def month_key(ym: Month) -> str:
    """アプリ内の月キー（先頭ゼロなし。例: 2026_8）。"""
    return f"{ym[0]}_{ym[1]}"


def _fmt(ym: Month) -> str:
    return f"{ym[0]}年{ym[1]}月"


def _mk(start: Month, end: Month, why: str) -> Period:
    span = _fmt(start) if start == end else f"{_fmt(start)}〜{_fmt(end)}"
    return Period(start, end, f"{span}（{why}）")


def _latest_season(season: str, today: Month) -> Tuple[Month, Month]:
    """今日より前に終わった、直近のその季節。"""
    s, e = _SEASONS[season]
    year = today[0]
    while True:
        start = (year - 1, s) if s > e else (year, s)  # 冬は 12 月が前年
        end = (year, e)
        if end < today:
            return start, end
        year -= 1


def _season_of(season: str, year: int) -> Tuple[Month, Month]:
    s, e = _SEASONS[season]
    return ((year - 1, s) if s > e else (year, s)), (year, e)


def _recent_month(m: int, today: Month) -> Month:
    """今日以前で、直近のその月。"""
    return (today[0], m) if (today[0], m) <= today else (today[0] - 1, m)


# 「去年の同じ月」「前年同月」「去年と比べて」: 期間ではなく、比べる相手の指定
_YOY = re.compile(r"(?:去年|昨年|前年)の?同(?:じ)?(?:月|時期)|(?:前年|昨年|去年)同月|(?:去年|昨年|前年)と(?:比べ|比較|くらべ)")


def parse_compare_shift(text: str) -> Optional[int]:
    """比べる相手が基準の月から何か月ずれているか。前年同月なら -12。指定がなければ None（前の月と比べる）。"""
    return -12 if _YOY.search(text.translate(_DIGITS)) else None


def parse_period(text: str, today: Optional[date] = None) -> Optional[Period]:
    t = _YOY.sub(" ", text.translate(_DIGITS))  # 比べる相手の指定は、基準の期間として読まない
    today = today or date.today()
    now: Month = (today.year, today.month)

    m = re.search(r"(\d{4})年(\d{1,2})月", t)
    if m:
        ym = (int(m[1]), int(m[2]))
        return _mk(ym, ym, "年月の指定")

    m = re.search(r"(\d{1,2})月?\s*(?:から|〜|~|-|ー)\s*(\d{1,2})月", t)
    if m:
        a, b = int(m[1]), int(m[2])
        year = now[0] if (now[0], b) <= now else now[0] - 1
        return _mk((year, a), (year, b), "月の範囲")

    m = re.search(r"(去年|昨年|今年|一昨年)\s*の?\s*(春|夏|秋|冬|(\d{1,2})月)?", t)
    if m:
        year = {"去年": now[0] - 1, "昨年": now[0] - 1, "今年": now[0], "一昨年": now[0] - 2}[m[1]]
        if m[2] in _SEASONS:
            s, e = _season_of(m[2], year)
            return _mk(s, e, f"{m[1]}の{m[2]}")
        if m[3]:
            ym = (year, int(m[3]))
            return _mk(ym, ym, f"{m[1]}の{m[3]}月")
        end = (year, 12) if year < now[0] else now
        return _mk((year, 1), end, f"{m[1]}")

    if "先々月" in t:
        ym = shift(now, -2)
        return _mk(ym, ym, "先々月")
    if "先月" in t or "前月" in t:
        ym = shift(now, -1)
        return _mk(ym, ym, "先月")
    if "今月" in t:
        return _mk(now, now, "今月")

    m = re.search(r"(?:直近|ここ|過去|最近)(\d{1,2})\s*(?:か|ヶ|ケ|カ)?月", t)
    if m:
        n = int(m[1])
        return _mk(shift(now, -(n - 1)), now, f"直近{n}か月")

    m = re.search(r"(春|夏|秋|冬)", t)
    if m:
        s, e = _latest_season(m[1], now)
        return _mk(s, e, f"直近の{m[1]}")

    m = re.search(r"(\d{1,2})月", t)
    if m and 1 <= int(m[1]) <= 12:
        ym = _recent_month(int(m[1]), now)
        return _mk(ym, ym, f"直近の{m[1]}月")

    return None


def clamp_to_available(period: Period, available: List[str]) -> Tuple[Month, Month, Optional[str]]:
    """データのある月の範囲に収める。収めた場合は、その旨の説明を返す。"""
    keys = [tuple(int(x) for x in k.split("_")) for k in available]
    first, last = min(keys), max(keys)
    start, end = max(period.start, first), min(period.end, last)
    note = None
    if period.end < first or period.start > last:
        start = end = last
        note = f"{period.label} はデータがないため、最新の {_fmt(last)} を使います"
    elif (start, end) != (period.start, period.end):
        note = f"データのある範囲（{_fmt(start)}〜{_fmt(end)}）に収めました"
    return start, end, note
