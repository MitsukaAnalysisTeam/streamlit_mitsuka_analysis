"""dataset.jsonl のラベルが、チャートカタログ（src/components/assistant/catalog.py）に収まっているかを検査する。

使い方: python benchmarks/nl_chart/validate_dataset.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.components.assistant.catalog import CATALOG, HIGHLIGHTS as _HL, validate_request  # noqa: E402

DATASET = Path(__file__).with_name("dataset.jsonl")

HIGHLIGHTS = set(_HL)
ACTIONS = {"run", "ask_back", "reject"}


def check_request(where, chart_id, args, errors):
    problem = validate_request(chart_id, args or {})
    if problem:
        errors.append(f"{where}: {problem}")


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
