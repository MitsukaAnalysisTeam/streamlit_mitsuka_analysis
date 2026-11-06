"""period.py の単体テスト。基準日は 2026-11-05。

使い方: python benchmarks/nl_chart/test_period.py
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.components.assistant.period import clamp_to_available, parse_compare_shift, parse_period  # noqa: E402

TODAY = date(2026, 11, 5)


def p(text):
    r = parse_period(text, TODAY)
    return None if r is None else (r.start, r.end)


def test_relative_months():
    assert p("先月の売上") == ((2026, 10), (2026, 10))
    assert p("先々月のランチ") == ((2026, 9), (2026, 9))
    assert p("今月は？") == ((2026, 11), (2026, 11))


def test_explicit():
    assert p("2025年3月の客数") == ((2025, 3), (2025, 3))
    assert p("２０２５年３月") == ((2025, 3), (2025, 3))
    assert p("9月の1日ごとの客数") == ((2026, 9), (2026, 9))
    assert p("12月の売上") == ((2025, 12), (2025, 12))  # 今年の12月はまだ来ていない


def test_ranges_and_seasons():
    assert p("3月から5月のラーメン") == ((2026, 3), (2026, 5))
    assert p("去年の夏") == ((2025, 6), (2025, 8))
    assert p("夏のラーメン") == ((2026, 6), (2026, 8))
    assert p("冬の売上") == ((2025, 12), (2026, 2))
    assert p("ここ3か月") == ((2026, 9), (2026, 11))
    assert p("去年") == ((2025, 1), (2025, 12))
    assert p("今年の客数") == ((2026, 1), (2026, 11))
    assert p("去年の3月") == ((2025, 3), (2025, 3))


def test_year_over_year():
    q = "先月の売り上げは去年の同じ月と比べるとどうなってる？"
    assert p(q) == ((2026, 10), (2026, 10))  # 去年は期間ではなく、比べる相手
    assert parse_compare_shift(q) == -12
    assert p("去年の同じ月と比べてどう？") is None  # 基準は指定なし（最新月になる）
    assert parse_compare_shift("去年の同じ月と比べてどう？") == -12
    assert parse_compare_shift("前年同月比は？") == -12
    assert p("9月は去年と比べてどう？") == ((2026, 9), (2026, 9))
    assert parse_compare_shift("9月は去年と比べてどう？") == -12
    assert parse_compare_shift("先月の売上") is None
    assert p("去年の夏の売上") == ((2025, 6), (2025, 8))  # 通常の去年は今までどおり


def test_none():
    assert p("売上見せて") is None


def test_clamp():
    avail = [f"2022_{m}" for m in range(10, 13)] + [f"2023_{m}" for m in range(1, 13)] + ["2026_10"]
    r = parse_period("今月は？", TODAY)
    assert clamp_to_available(r, avail)[:2] == ((2026, 10), (2026, 10))
    assert clamp_to_available(r, avail)[2] is not None
    r = parse_period("ここ3か月", TODAY)
    assert clamp_to_available(r, avail)[:2] == ((2026, 9), (2026, 10))  # 終わりだけ最新月に収まる


if __name__ == "__main__":
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in tests:
        fn()
        print("ok", name)
    print(f"{len(tests)} tests passed")
