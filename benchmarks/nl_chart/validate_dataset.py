"""dataset.jsonl のラベルが、チャートカタログの語彙に収まっているかを検査する。

使い方: python benchmarks/nl_chart/validate_dataset.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).with_name("dataset.jsonl")

DAILY_COLUMNS = ["売上(昼)", "客数(昼)", "客単価(昼)", "売上(夜)", "客数(夜)", "客単価(夜)",
                 "1日総売上", "1日総客数", "1日客単価"]
WEEKDAYS = ["全体", "水", "木", "金", "土", "日"]

# chart_id -> {引数名: 取りうる値}。期間は args に含めず、period で別に持つ
CATALOG = {
    "daily_bar": {"metric": ["売上", "客数", "客単価"]},
    "hourly_bar": {"metric": ["売上", "客数"], "weekday": WEEKDAYS},
    "hourly_compare": {"metric": ["売上", "客数"], "weekday_a": WEEKDAYS, "weekday_b": WEEKDAYS},
    "monthly_sum": {"item": [c for c in DAILY_COLUMNS if "客単価" not in c]},
    "monthly_mean": {"item": DAILY_COLUMNS},
    "weekly_compare": {"item": DAILY_COLUMNS},
    "yearly_bar": {"metric": ["合計客数", "合計売上", "平均客数", "平均売上", "平均客単価"]},
    "ramen_pie": {"slot": ["昼", "夜", "深夜", "全体"], "mode": ["販売数", "売上"]},
    "ramen_weekday_bar": {"slot": ["昼", "夜", "深夜", "全体"], "mode": ["販売数", "売上"]},
    "lunch_pie": {"breakdown": ["カテゴリ別", "セットメニュー内訳"], "mode": ["販売数", "売上"]},
    "alcohol_trend": {"kind": ["アルコール合計", "ビール", "秋鹿", "若尾ワイン"],
                      "metric": ["平均杯数", "合計売上"]},
}
HIGHLIGHTS = {"max", "min", "biggest_change", "none"}
ACTIONS = {"run", "ask_back", "reject"}


def check_request(where, chart_id, args, errors):
    if chart_id not in CATALOG:
        errors.append(f"{where}: 未知の chart_id {chart_id!r}")
        return
    spec = CATALOG[chart_id]
    if set(args or {}) != set(spec):
        errors.append(f"{where}: 引数名が {sorted(spec)} と一致しない: {sorted(args or {})}")
        return
    for name, value in args.items():
        if value not in spec[name]:
            errors.append(f"{where}: {chart_id}.{name} に範囲外の値 {value!r}")


def main():
    rows = [json.loads(line) for line in DATASET.read_text(encoding="utf-8").splitlines() if line]
    errors = []
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("id が重複している")

    for r in rows:
        where = r["id"]
        e = r["expected"]
        if r["split"] not in {"dev", "eval"}:
            errors.append(f"{where}: split が不正")
        if e["action"] not in ACTIONS:
            errors.append(f"{where}: action が不正")
        if e["highlight"] not in HIGHLIGHTS:
            errors.append(f"{where}: highlight が不正")
        if e["answerable"] != (e["action"] != "reject"):
            errors.append(f"{where}: answerable と action が矛盾")
        if e["action"] == "run":
            check_request(where, e["chart_id"], e["args"], errors)
        elif e["action"] == "ask_back":
            if not e["candidates"] or any(c not in CATALOG for c in e["candidates"]):
                errors.append(f"{where}: candidates が不正")
        elif e["chart_id"] is not None:
            errors.append(f"{where}: reject なのに chart_id がある")
        prev = r["previous_request"]
        if prev:
            check_request(f"{where}(previous)", prev["chart_id"], prev["args"], errors)

    print(f"{len(rows)} 件")
    print("split:", dict(Counter(r["split"] for r in rows)))
    print("category:", dict(Counter(r["category"] for r in rows)))
    print("chart_id:", dict(Counter(r["expected"]["chart_id"] for r in rows if r["expected"]["chart_id"])))
    missing = [c for c in CATALOG
               if sum(1 for r in rows if r["expected"]["chart_id"] == c) < 3]
    if missing:
        errors.append(f"3 件未満のチャート: {missing}")
    for msg in errors:
        print("NG:", msg)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
