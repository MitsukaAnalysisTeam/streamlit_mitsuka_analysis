"""results/ の保存結果を採点して、読みやすい表にまとめる（API は呼ばない）。

使い方:
  python benchmarks/nl_chart/evaluate.py                       # results/ の dev を全部（smoke は除く）
  python benchmarks/nl_chart/evaluate.py results/jev__*.jsonl   # ファイル指定
  python benchmarks/nl_chart/evaluate.py --detail               # 外れた質問の一覧も出す

判断役（jev / decisions）は、しきい値を当てた振り分け（route）の結果で採点する。質問を 2 種類に分けて見る。
- 実行すべき質問: 正しく実行できたか、聞き返し・LLM に回ったか、誤って実行したか
- 実行すべきでない質問（曖昧・対応外）: 聞き返し/対応外にできたか、LLM に回ったか、誤って実行したか（危険）
"""
import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as c  # noqa: E402

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset.jsonl"
RESULTS = HERE / "results"
OUT = RESULTS / "report.md"
JUDGES = ("jev", "decisions")


def load_rows():
    return {r["id"]: r for r in (json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l)}


def load_records(paths):
    recs = []
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line:
                recs.append(json.loads(line))
    return recs


def predict(rec):
    return c.prediction_from_raw(rec["adapter"], rec["raw"])


def classify(exp, final):
    """振り分け結果を、期待に照らして分類する。"""
    if exp["action"] == "run":
        if final.action == "run":
            ok = final.chart_id == exp["chart_id"] and final.args == exp["args"] and final.highlight == exp["highlight"]
            return "run_ok" if ok else "run_wrong"
        return {"ask_back": "run_asked", "fallback": "run_llm", "reject": "run_rejected"}[final.action]
    if final.action == exp["action"]:
        return "non_ok"
    return "non_unsafe" if final.action == "run" else "non_llm" if final.action == "fallback" else "non_other"


def breakdown(recs, rows, **route_kw):
    cnt = Counter()
    misses = []
    for r in recs:
        if r.get("error"):
            cnt["error"] += 1
            continue
        exp = rows[r["id"]]["expected"]
        final = c.judge_to_final(predict(r), **route_kw)
        kind = classify(exp, final)
        cnt[kind] += 1
        cnt["run_n" if exp["action"] == "run" else "non_n"] += 1
        if kind in ("run_wrong", "non_unsafe", "run_rejected"):
            misses.append((r["id"], rows[r["id"]]["question"], exp, final, kind))
    return cnt, misses


def pct(a, b):
    return f"{a / b * 100:.0f}%" if b else "-"


def table(groups, rows, with_fit, detail_out):
    head = ["設定", "正しく実行", "聞き返し", "LLMへ", "誤って実行", "│", "正解(聞き返し/対応外)", "LLMへ", "**危険な実行**", "LLMへ回る合計"]
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    t_fits = [None, 0.3, 0.4, 0.5] if with_fit else [None]
    for t_fit in t_fits:
        for inc_hl in (True, False):
            cnt, misses = breakdown(groups, rows, include_highlight=inc_hl, t_fit=t_fit)
            rn, nn = cnt["run_n"], cnt["non_n"]
            llm = cnt["run_llm"] + cnt["non_llm"]
            label = f"強調{'含む' if inc_hl else '除く'}" + (f" / 使えるか<{t_fit}" if t_fit is not None else "")
            out.append("| " + " | ".join([
                label, pct(cnt["run_ok"], rn), pct(cnt["run_asked"], rn), pct(cnt["run_llm"], rn),
                pct(cnt["run_wrong"] + cnt["run_rejected"], rn), "│",
                pct(cnt["non_ok"], nn), pct(cnt["non_llm"], nn), f"**{pct(cnt['non_unsafe'], nn)}** ({cnt['non_unsafe']})",
                pct(llm, rn + nn)]) + " |")
            if detail_out is not None and inc_hl and t_fit == (0.4 if with_fit else None):
                detail_out.extend(misses)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()
    files = args.files or sorted(str(p) for p in RESULTS.glob("*__dev__*.jsonl") if "smoke" not in p.name)
    if not files:
        sys.exit("results/ に対象のファイルがありません")
    rows = load_rows()
    recs = [r for r in load_records(files) if r["adapter"] in JUDGES]

    groups = defaultdict(list)
    for r in recs:
        groups[(r["adapter"], r["model"], r["with_none"], r.get("with_fit", False))].append(r)

    out = ["# ベンチマーク結果（自動生成）", "",
           "- 1 行 = ある設定での、質問 × 選択肢の順序（3 通り）の集計。しきい値は仮置き（0.2 / 0.5 / 0.8）",
           "- **実行すべき質問**: 正しく実行できたか。「聞き返し」「LLMへ」は安全側の外れ。「誤って実行」は別の設定で実行、または対応外にした場合",
           "- **実行すべきでない質問**（曖昧・対応外）: 「危険な実行」は、聞き返し・対応外にすべきものを実行してしまった割合（0 が理想）",
           "- **使えるか<t**: 選んだグラフが質問に使えるかの確率が t 未満なら LLM に回す（「使えるか」を聞いた実行のみ）", ""]

    detail = []
    for (adapter, model, with_none, with_fit), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][3], kv[0][2])):
        title = f"{adapter} / {model} / 該当なし{'あり' if with_none else 'なし'} / 使えるかの質問{'あり' if with_fit else 'なし'}"
        out += [f"## {title}", ""]
        sub = []
        out += table(rs, rows, with_fit, sub)
        detail.append((title, sub))

        lat = [r["latency_s"] for r in rs if not r.get("error")]
        tok = [r["usage"].get("input_tokens") or 0 for r in rs if r.get("usage")]
        by_q = defaultdict(set)
        for r in rs:
            if not r.get("error"):
                by_q[r["id"]].add(predict(r).chart_id)
        unstable = sum(1 for v in by_q.values() if len(v) > 1)
        out += ["", f"- 選択肢の順序でグラフの答えが変わった質問: {unstable} / {len(by_q)}",
                f"- 応答時間: 中央値 {statistics.median(lat):.2f}s / 入力 平均 {statistics.mean(tok):,.0f} トークン", ""]

    if args.detail:
        out += ["## 外れた質問（強調を含む・使えるか<0.4、順序違いは重複を除く）", ""]
        for title, misses in detail:
            out.append(f"### {title}")
            seen = set()
            for qid, q, exp, final, kind in misses:
                key = (qid, kind, final.chart_id)
                if key in seen:
                    continue
                seen.add(key)
                out.append(f"- {qid} 「{q}」 期待={exp['action']}/{exp['chart_id']} → 結果={final.action}/{final.chart_id}"
                           f"{'  ⚠危険な実行' if kind == 'non_unsafe' else ''}")
            out.append("")

    text = "\n".join(out)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n(保存先: {OUT})")


if __name__ == "__main__":
    main()
