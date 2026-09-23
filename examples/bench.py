#!/usr/bin/env python3
"""
Decision-model benchmark harness.

Runs the same labeled examples against Jev (via OpenRouter) and your own
endpoint, then compares accuracy, calibration (ECE / Brier), latency, and cost.

SETUP
    pip install requests
    export OPENROUTER_API_KEY=...                       # for Jev
    export YOURS_URL=http://localhost:8000/v1/decisions # your server (same request/response shape as Jev)
    export YOURS_KEY=...                                # optional

RUN
    python bench.py sample.jsonl --targets jev                # baseline only
    python bench.py sample.jsonl --targets jev yours          # head to head
    python bench.py mydata.jsonl --targets jev yours --workers 8

DATASET (JSONL, one example per line)
    {"id": "t1", "type": "choice", "state": "...", "instructions": "...",
     "criteria": {"billing": "Charges, refunds", "technical": "Bugs"}, "label": "billing"}
    {"id": "t2", "type": "noul", "state": "...", "instructions": "...", "label": true}
    {"id": "t3", "type": "score", "state": "...", "instructions": "...",
     "criteria": ["Low", "Medium", "High"], "label": 2}

NOTES
    * "state" may be a string or a JSON object/array.
    * Score labels are the index of the rubric level. If Jev's scores turn out to be
      1-based, rerun with --score-base 1 (check with one manual call first).
    * Read TypeSafe's terms before publishing benchmark results, and never train
      on Jev's outputs.
    * Env overrides: JEV_MODEL, JEV_PRICE_PER_M, YOURS_MODEL, YOURS_PRICE_PER_M.
"""

import argparse
import csv
import json
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

TARGETS = {
    "jev": {
        "url": "https://openrouter.ai/api/alpha/decisions",
        "key_env": "OPENROUTER_API_KEY",
        "model": os.getenv("JEV_MODEL", "~typesafe/jev-latest"),
        "price_per_m": float(os.getenv("JEV_PRICE_PER_M", "0.042")),
    },
    "axiom": {
        "url": os.getenv("AXIOM_URL", "http://localhost:8000/v1/decisions"),
        "key_env": "AXIOM_KEY",
        "model": os.getenv("AXIOM_MODEL", "axiom-v1"),
        "price_per_m": float(os.getenv("AXIOM_PRICE_PER_M", "0.000")),
    },
    "yours": {
        "url": os.getenv("YOURS_URL", "http://localhost:8000/v1/decisions"),
        "key_env": "YOURS_KEY",
        "model": os.getenv("YOURS_MODEL", "axiom-v1"),
        "price_per_m": float(os.getenv("YOURS_PRICE_PER_M", "0.000")),
    },
}


# ---------------------------------------------------------------- requests
def build_question(ex):
    q = {"type": ex["type"], "instructions": ex["instructions"]}
    if ex.get("criteria") is not None:
        q["criteria"] = ex["criteria"]
    return q


def call(cfg, ex, timeout):
    headers = {"Content-Type": "application/json"}
    key = os.getenv(cfg["key_env"])
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = {
        "model": cfg["model"],
        "state": ex["state"],
        "questions": {"q": build_question(ex)},
    }
    t0 = time.perf_counter()
    r = requests.post(cfg["url"], headers=headers, json=body, timeout=timeout)
    latency = time.perf_counter() - t0
    r.raise_for_status()
    data = r.json()
    return data["answers"]["q"], data.get("usage", {}), latency


# ---------------------------------------------------------------- scoring
def confidence_of(ans):
    c = ans.get("confidence")
    if isinstance(c, (int, float)):
        return float(c)
    probs = ans.get("probabilities")
    if isinstance(probs, dict) and probs:
        return float(max(probs.values()))
    if isinstance(probs, list) and probs:
        return float(max(probs))
    return None


def evaluate(ex, ans, score_base):
    t = ex["type"]
    if t == "choice":
        pred = ans.get("choice")
        return {"pred": pred, "correct": pred == ex["label"], "conf": confidence_of(ans)}
    if t == "noul":
        p = float(ans["noul"])
        label = 1.0 if ex["label"] else 0.0
        return {
            "pred": round(p, 4),
            "correct": (p >= 0.5) == bool(ex["label"]),
            "conf": max(p, 1 - p),
            "brier": (p - label) ** 2,
        }
    if t == "score":
        s = float(ans["score"]) - score_base
        return {
            "pred": round(s, 3),
            "correct": round(s) == ex["label"],
            "conf": confidence_of(ans),
            "abs_err": abs(s - ex["label"]),
        }
    raise ValueError(f"unknown type: {t}")


def run_target(cfg, examples, workers, timeout, score_base):
    def one(ex):
        base = {"id": ex["id"], "type": ex["type"], "label": ex["label"]}
        for attempt in range(3):
            try:
                ans, usage, lat = call(cfg, ex, timeout)
                out = evaluate(ex, ans, score_base)
                return {
                    **base,
                    **out,
                    "latency_s": lat,
                    "input_tokens": usage.get("input_tokens", 0),
                    "error": None,
                }
            except requests.HTTPError as e:
                code = e.response.status_code if e.response is not None else 0
                if code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                return {**base, "error": f"HTTP {code}"}
            except Exception as e:  # network, parse, missing fields
                if attempt < 2:
                    time.sleep(1.0)
                    continue
                return {**base, "error": f"{type(e).__name__}: {e}"[:200]}
        return {**base, "error": "unknown"}

    rows = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(one, ex) for ex in examples]
        for f in as_completed(futures):
            rows.append(f.result())
    rows.sort(key=lambda r: str(r["id"]))
    return rows


# ---------------------------------------------------------------- metrics
def ece(pairs, bins=10):
    pairs = [(c, k) for c, k in pairs if c is not None]
    if not pairs:
        return None
    total, e = len(pairs), 0.0
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        bucket = [(c, k) for c, k in pairs if lo <= c < hi or (b == bins - 1 and c >= 1.0)]
        if bucket:
            acc = sum(k for _, k in bucket) / len(bucket)
            conf = sum(c for c, _ in bucket) / len(bucket)
            e += len(bucket) / total * abs(acc - conf)
    return e


def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    return s[int(round(p * (len(s) - 1)))]


def summarize(rows, price_per_m):
    ok = [r for r in rows if not r.get("error")]
    out = {"n": len(rows), "errors": len(rows) - len(ok)}
    if not ok:
        return out
    out["accuracy"] = sum(r["correct"] for r in ok) / len(ok)
    out["ece"] = ece([(r["conf"], 1.0 if r["correct"] else 0.0) for r in ok])
    briers = [r["brier"] for r in ok if "brier" in r]
    out["brier_noul"] = statistics.mean(briers) if briers else None
    errs = [r["abs_err"] for r in ok if "abs_err" in r]
    out["score_mae"] = statistics.mean(errs) if errs else None
    lats = [r["latency_s"] * 1000 for r in ok]
    out["p50_ms"], out["p95_ms"] = pct(lats, 0.5), pct(lats, 0.95)
    toks = [r["input_tokens"] for r in ok]
    out["avg_in_tokens"] = statistics.mean(toks)
    out["usd_per_1k"] = out["avg_in_tokens"] * 1000 * price_per_m / 1e6
    return out


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.3f}" if abs(v) < 10 else f"{v:.0f}"
    return str(v)


COLUMNS = ["n", "errors", "accuracy", "ece", "brier_noul", "score_mae",
           "p50_ms", "p95_ms", "avg_in_tokens", "usd_per_1k"]


def print_report(name, rows, price_per_m):
    print(f"\n=== {name} ===")
    print(f"{'group':8} " + " ".join(f"{c:>13}" for c in COLUMNS))
    groups = [("all", rows)] + [
        (t, [r for r in rows if r["type"] == t]) for t in ("choice", "noul", "score")
    ]
    for label, subset in groups:
        if not subset:
            continue
        s = summarize(subset, price_per_m)
        print(f"{label:8} " + " ".join(f"{fmt(s.get(c)):>13}" for c in COLUMNS))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Benchmark decision models on labeled examples.")
    ap.add_argument("dataset", help="path to JSONL dataset")
    ap.add_argument("--targets", nargs="+", default=["jev"], choices=list(TARGETS))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--limit", type=int, default=0, help="only run the first N examples")
    ap.add_argument("--score-base", type=int, default=0,
                    help="0 if the model's score is a 0-based level index, 1 if 1-based")
    ap.add_argument("--out", default="bench_out", help="output directory")
    args = ap.parse_args()

    with open(args.dataset, encoding="utf-8") as f:
        examples = [json.loads(line) for line in f if line.strip()]
    if args.limit:
        examples = examples[: args.limit]
    if not examples:
        sys.exit("No examples found in dataset.")

    os.makedirs(args.out, exist_ok=True)
    for name in args.targets:
        cfg = TARGETS[name]
        if name == "jev" and not os.getenv(cfg["key_env"]):
            sys.exit(f"Set {cfg['key_env']} to benchmark Jev.")
        print(f"Running {len(examples)} examples against {name} ({cfg['model']}) ...")
        rows = run_target(cfg, examples, args.workers, args.timeout, args.score_base)
        print_report(name, rows, cfg["price_per_m"])

        path = os.path.join(args.out, f"results_{name}.csv")
        fields = sorted({k for r in rows for k in r})
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        print(f"Per-example results: {path}")

        failed = [r for r in rows if r.get("error")]
        if failed:
            print(f"{len(failed)} failed, first error: {failed[0]['error']}")


if __name__ == "__main__":
    main()
