"""モデルに質問セットを投げて、生の応答を results/ に JSONL で保存する。

採点・しきい値の比較は保存した応答から後で計算する（evaluate.py）。ここでは API を呼ぶだけ。

例:
  # 中身の確認だけ（API は呼ばない・キー不要）
  python benchmarks/nl_chart/run.py --adapter jev --model jev-latest --split dev --dry-run

  # Jev 1.13 を dev 30 件で。選択肢の順序なし／シャッフル 2 通り、「該当なし」あり・なし
  python benchmarks/nl_chart/run.py --adapter jev --model jev-latest --split dev \
      --shuffle-seeds none 1 2 --with-none both

  # Decisions API
  python benchmarks/nl_chart/run.py --adapter decisions --model gpt-6-luna --split dev

  # フォールバック LLM: GPT-6 Luna（関数呼び出し）。同じ質問を 3 回（再実行の一致を見る）
  python benchmarks/nl_chart/run.py --adapter openai --model gpt-6-luna --split dev --repeat 3

  # Claude Haiku 5.5（Anthropic のキーがあるとき）
  python benchmarks/nl_chart/run.py --adapter claude --model claude-haiku-5-5 --split dev --repeat 3
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import common as c
from adapters.claude import ClaudeAdapter
from adapters.http_judges import DecisionsAdapter, JevAdapter
from adapters.openai_llm import OpenAILLMAdapter

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset.jsonl"
RESULTS = HERE / "results"

ADAPTERS = {"jev": JevAdapter, "decisions": DecisionsAdapter, "openai": OpenAILLMAdapter, "claude": ClaudeAdapter}
LLM_ADAPTERS = ("openai", "claude")


def load_dataset(split: str, limit: Optional[int] = None, path: Path = DATASET) -> List[Dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    if split != "all":
        rows = [r for r in rows if r["split"] == split]
    return rows[:limit] if limit else rows


def parse_seeds(values: List[str]) -> List[Optional[int]]:
    return [None if v == "none" else int(v) for v in values]


def parse_with_none(value: str) -> List[bool]:
    return {"yes": [True], "no": [False], "both": [False, True]}[value]


def plan(rows, with_nones, seeds, repeat) -> Iterator[Tuple[Dict[str, Any], bool, Optional[int], int]]:
    """実行する (質問, with_none, seed, repeat 番号) の一覧。"""
    for with_none in with_nones:
        for seed in seeds:
            for rep in range(repeat):
                for row in rows:
                    yield row, with_none, seed, rep


def run_one(adapter, row, with_none, seed, rep) -> Dict[str, Any]:
    rec = {
        "id": row["id"],
        "adapter": adapter.kind,
        "model": adapter.model,
        "with_none": with_none,
        "shuffle_seed": seed,
        "repeat": rep,
        "ts": datetime.now().isoformat(timespec="seconds"),
    }
    start = time.perf_counter()
    try:
        rec.update(adapter.call(row, with_none, seed))
    except Exception as e:  # noqa: BLE001  1件の失敗で全体を止めず、記録して続ける
        rec["error"] = f"{type(e).__name__}: {e}"[:500]
    rec["latency_s"] = round(time.perf_counter() - start, 3)
    return rec


def run_all(adapter, jobs, workers: int, out) -> Tuple[int, int]:
    """全ジョブを実行して out に1行ずつ書く。(成功数, 失敗数) を返す。"""
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(run_one, adapter, *job) for job in jobs]
        for i, fut in enumerate(futures, 1):
            rec = fut.result()
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            if "error" in rec:
                failed += 1
            else:
                ok += 1
            if i % 20 == 0:
                print(f"  {i}/{len(futures)}", file=sys.stderr)
    return ok, failed


def make_adapter(name: str, model: str, effort: Optional[str] = None):
    cls = ADAPTERS[name]
    if name in LLM_ADAPTERS:
        return cls(model=model, **({"effort": effort} if effort else {}))
    return cls(model)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", choices=list(ADAPTERS), required=True)
    ap.add_argument("--model", required=True, help="例: jev-latest / jev-preview / gpt-6-luna / claude-haiku-5-5（--adapter decisions と openai はどちらも gpt-6-luna）")
    ap.add_argument("--split", choices=["dev", "eval", "all"], default="dev")
    ap.add_argument("--limit", type=int, help="先頭から N 件だけ（動作確認用）")
    ap.add_argument("--shuffle-seeds", nargs="+", default=["none"], metavar="SEED",
                    help="選択肢の順序。none=シャッフルなし、整数=その seed でシャッフル。複数指定で複数回（判断役のみ）")
    ap.add_argument("--with-none", choices=["yes", "no", "both"], default="no",
                    help="チャートの選択肢に「どれも当てはまらない」を足すか（判断役のみ）")
    ap.add_argument("--effort", help="LLM の思考の量（openai / claude のみ。既定は low）")
    ap.add_argument("--repeat", type=int, default=1, help="同じリクエストを何回投げるか（再実行の一致を見る）")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tag", default="", help="出力ファイル名に付ける識別子")
    ap.add_argument("--dry-run", action="store_true", help="API を呼ばず、リクエストの内容と回数だけ表示する")
    args = ap.parse_args(argv)

    rows = load_dataset(args.split, args.limit)
    is_judge = args.adapter in ("jev", "decisions")
    seeds = parse_seeds(args.shuffle_seeds) if is_judge else [None]
    with_nones = parse_with_none(args.with_none) if is_judge else [False]
    jobs = list(plan(rows, with_nones, seeds, args.repeat))
    adapter = make_adapter(args.adapter, args.model, args.effort)

    first = jobs[0]
    body = adapter.build_request(first[0], first[1], first[2])
    body_json = json.dumps(body, ensure_ascii=False)
    print(f"{args.adapter} / {args.model} / split={args.split}: {len(rows)} 問 × "
          f"{len(jobs) // max(len(rows), 1)} 通り = {len(jobs)} リクエスト")
    print(f"1 リクエストの本文: {len(body_json):,} 文字")
    if args.dry_run:
        print("--- 最初のリクエスト（--dry-run: API は呼んでいません）---")
        print(json.dumps(body, ensure_ascii=False, indent=2)[:3000] + "\n...")
        return 0

    c.require_key(adapter.key_env)  # 走らせ始める前に、キーの有無を確認する
    RESULTS.mkdir(exist_ok=True)
    name = "__".join(p for p in [args.adapter, args.model, args.split, args.tag,
                                 datetime.now().strftime("%Y%m%d-%H%M%S")] if p)
    path = RESULTS / f"{name}.jsonl"
    with path.open("w", encoding="utf-8") as out:
        ok, failed = run_all(adapter, jobs, args.workers, out)
    print(f"完了: 成功 {ok} / 失敗 {failed} → {path}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
