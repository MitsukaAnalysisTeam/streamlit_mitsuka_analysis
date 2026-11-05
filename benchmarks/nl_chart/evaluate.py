"""results/ の保存結果を採点して、読みやすい表にまとめる（API は呼ばない）。

使い方:
  python benchmarks/nl_chart/evaluate.py                       # results/ の dev を全部（smoke は除く）
  python benchmarks/nl_chart/evaluate.py results/jev__*.jsonl   # ファイル指定
  python benchmarks/nl_chart/evaluate.py --detail               # 外れた質問の一覧も出す

判断役（jev / decisions）は route() でしきい値を当てた最終動作で採点する。
"fallback"（LLM に回す）になった質問は、判断役だけでは決まらなかったものとして別に数える。
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


def load_rows():
    return {r["id"]: r for r in (json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l)}


def load_records(paths):
    recs = []
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            if line:
                recs.append(json.loads(line))
    return recs


def judge(exp, final):
    """(分類, 完全一致か) を返す。分類: ok / wrong / unsafe_run / fallback"""
    if final.action == "fallback":
        return "fallback", False
    if final.action != exp["action"]:
        # 対応外・曖昧なのに実行してしまうのは重い誤り
        return ("unsafe_run" if final.action == "run" else "wrong"), False
    if exp["action"] == "run":
        ok = (final.chart_id == exp["chart_id"] and final.args == exp["args"]
              and final.highlight == exp["highlight"])
        return ("ok" if ok else "wrong"), ok
    return "ok", True


def score_group(recs, rows, **route_kw):
    stats = Counter()
    chart_hit = chart_n = 0
    misses = []
    for r in recs:
        if r.get("error"):
            stats["error"] += 1
            continue
        exp = rows[r["id"]]["expected"]
        pred = c.assemble_judge_prediction(c.parse_jev_response(r["raw"])) if r["adapter"] == "jev" else \
            c.assemble_judge_prediction(c.parse_decisions_response(r["raw"]))
        final = c.judge_to_final(pred, **route_kw)
        kind, _ = judge(exp, final)
        stats[kind] += 1
        stats["n"] += 1
        if exp["action"] == "run":
            chart_n += 1
            chart_hit += pred.chart_id == exp["chart_id"]
        if kind in ("wrong", "unsafe_run"):
            misses.append((r["id"], rows[r["id"]]["question"], exp, final, kind))
    return stats, chart_hit, chart_n, misses


def pct(a, b):
    return f"{a / b * 100:.0f}%" if b else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()
    files = args.files or sorted(str(p) for p in RESULTS.glob("*__dev__dev__*.jsonl"))
    if not files:
        sys.exit("results/ に対象のファイルがありません")
    rows = load_rows()
    recs = load_records(files)

    groups = defaultdict(list)
    for r in recs:
        groups[(r["adapter"], r["model"])].append(r)

    out = ["# ベンチマーク結果（自動生成）", "",
           "- 行 = 質問 × 選択肢の順序 3 通り × 「該当なし」あり/なし。しきい値は設計書の仮置き（0.2 / 0.5 / 0.8）",
           "- **確定** = 判断役だけで run / 聞き返し / 対応外 が決まった割合。**LLM へ** = 自信が低く LLM に回す割合",
           "- **確定の中の正解率** = 確定したもののうち、期待どおりだった割合（高いほど安心して任せられる）",
           "- **危険な実行** = 対応外や曖昧な質問を、そのまま実行してしまった件数（0 が理想）", ""]

    for (adapter, model), rs in sorted(groups.items()):
        if adapter not in ("jev", "decisions"):
            continue
        out += [f"## {adapter} / {model}", "",
                "| 設定 | 件数 | 確定 | LLMへ | 確定の中の正解率 | 危険な実行 | チャート正答 |",
                "|---|---|---|---|---|---|---|"]
        all_misses = []
        for with_none in ("no", "yes"):
            for inc_hl in (True, False):
                sub = [r for r in rs if r["with_none"] == (with_none == "yes")]
                st, ch, cn, ms = score_group(sub, rows, include_highlight=inc_hl)
                n = st["n"]
                decided = st["ok"] + st["wrong"] + st["unsafe_run"]
                label = f"該当なし{'あり' if with_none == 'yes' else 'なし'} / 強調{'を判定に含める' if inc_hl else 'は判定に含めない'}"
                out.append(f"| {label} | {n} | {pct(decided, n)} | {pct(st['fallback'], n)} | "
                           f"{pct(st['ok'], decided)} | {st['unsafe_run']} | {pct(ch, cn)} |")
                if with_none == "no" and inc_hl:
                    all_misses = ms
        out.append("")

        # 順序への耐性: 同じ質問で、順序によってチャートが変わった割合
        by_q = defaultdict(set)
        for r in rs:
            if r["with_none"] is False and not r.get("error"):
                p = c.assemble_judge_prediction(c.parse_jev_response(r["raw"])) if adapter == "jev" else \
                    c.assemble_judge_prediction(c.parse_decisions_response(r["raw"]))
                by_q[r["id"]].add(p.chart_id)
        unstable = sum(1 for v in by_q.values() if len(v) > 1)
        lat = [r["latency_s"] for r in rs if not r.get("error")]
        tok = [r["usage"].get("input_tokens", 0) for r in rs if r.get("usage")]
        out += [f"- 選択肢の順序でチャートの答えが変わった質問: **{unstable} / {len(by_q)}**",
                f"- 応答時間: 中央値 {statistics.median(lat):.2f}s / 最大 {max(lat):.2f}s",
                f"- 入力トークン: 平均 {statistics.mean(tok):,.0f}（1,000 回あたり約 ${statistics.mean(tok) * 0.042 / 1000:.2f}、Jev の単価の場合）" if tok else "",
                ""]

        # 信頼度の区間ごとの正解率（該当なしなし・順序なし）
        base = [r for r in rs if r["with_none"] is False and r["shuffle_seed"] is None and not r.get("error")]
        buckets = defaultdict(lambda: [0, 0])
        for r in base:
            exp = rows[r["id"]]["expected"]
            p = c.assemble_judge_prediction(c.parse_jev_response(r["raw"])) if adapter == "jev" else \
                c.assemble_judge_prediction(c.parse_decisions_response(r["raw"]))
            if exp["action"] != "run" or p.chart_conf is None:
                continue
            b = "0.9以上" if p.chart_conf >= 0.9 else "0.8〜0.9" if p.chart_conf >= 0.8 else "0.5〜0.8" if p.chart_conf >= 0.5 else "0.5未満"
            buckets[b][0] += p.chart_id == exp["chart_id"]
            buckets[b][1] += 1
        out += ["チャートの confidence ごとの正解率（実行すべき質問のみ）:", "",
                "| confidence | 件数 | 正解率 |", "|---|---|---|"]
        for b in ("0.9以上", "0.8〜0.9", "0.5〜0.8", "0.5未満"):
            h, n = buckets[b]
            out.append(f"| {b} | {n} | {pct(h, n)} |")
        out.append("")

        if args.detail:
            out += ["外れた質問（該当なしなし・強調を含める、順序ごとに重複あり）:", ""]
            seen = set()
            for qid, q, exp, final, kind in all_misses:
                if (qid, kind, final.chart_id) in seen:
                    continue
                seen.add((qid, kind, final.chart_id))
                out.append(f"- {qid} 「{q}」 期待={exp['action']}/{exp['chart_id']}{exp['args']}/{exp['highlight']} "
                           f"→ 結果={final.action}/{final.chart_id}{final.args}/{final.highlight}"
                           f"{'  ⚠危険な実行' if kind == 'unsafe_run' else ''}")
            out.append("")

    text = "\n".join(out)
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n(保存先: {OUT})")


if __name__ == "__main__":
    main()
