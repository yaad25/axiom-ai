#!/usr/bin/env python3
"""
Reference implementation of "best flight from A to B in 2-5 seconds"
(implementation plan, Section 2b).

Pipeline:
  1. Parse the request (rule-based here; swap in your model if needed)
  2. Fetch offers from a flight-data API (mocked here; wire in Duffel for real data)
  3. Rank with a weighted formula (fast, no model call)
  4. Optionally re-rank the top N with the decision server for soft
     preferences ("avoid red-eyes", "prefer a good airline")
  5. Return within a hard time budget

Run (mock data, no keys needed):
    python flight_demo.py "flight from DEL to DXB tomorrow, avoid red-eyes"

Run with the decide server for soft-preference re-ranking:
    # in another terminal: uvicorn app:app --port 8000  (from ../server)
    DECIDE_URL=http://localhost:8000 python flight_demo.py "..." --soft

To wire in real data, replace `fetch_offers_mock` with a call to Duffel's
offer request endpoint (https://duffel.com/docs) and keep everything else
the same — the budget/ranking/re-rank logic doesn't change.
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
from dataclasses import dataclass, field

import requests

HARD_TIMEOUT_S = 3.0          # flight-source search budget (plan: 1-4s, bottleneck)
TOTAL_BUDGET_S = 5.0          # end-to-end budget
DECIDE_URL = os.getenv("DECIDE_URL", "")  # set to re-rank with soft preferences


# --------------------------------------------------------------- step 1
@dataclass
class ParsedQuery:
    origin: str
    destination: str
    date_hint: str
    avoid_red_eyes: bool = False
    prefer_good_airline: bool = False


IATA_RE = re.compile(r"\b([A-Z]{3})\b")


def parse_query(text: str) -> ParsedQuery:
    """Toy parser: pulls two IATA-looking codes and a couple of preference
    keywords. Replace with a real NLU step or your model for production."""
    codes = IATA_RE.findall(text.upper())
    origin, destination = (codes + ["DEL", "DXB"])[:2]
    return ParsedQuery(
        origin=origin,
        destination=destination,
        date_hint="tomorrow" if "tomorrow" in text.lower() else "unspecified",
        avoid_red_eyes="red-eye" in text.lower() or "red eye" in text.lower(),
        prefer_good_airline="good airline" in text.lower() or "best airline" in text.lower(),
    )


# --------------------------------------------------------------- step 2
@dataclass
class Offer:
    airline: str
    price_usd: float
    duration_min: int
    stops: int
    departs_hour: int  # 0-23, local
    id: str = field(default_factory=lambda: f"of_{random.randint(1000, 9999)}")


AIRLINES = ["IndiGo", "Emirates", "Air India", "Vistara", "flydubai", "Qatar Airways"]


def fetch_offers_mock(q: ParsedQuery, n: int = 40) -> list[Offer]:
    """Stand-in for a real flight-data API call (Duffel etc).
    Simulates realistic network latency inside the hard timeout."""
    time.sleep(random.uniform(0.8, 1.6))  # pretend network latency
    offers = []
    for _ in range(n):
        stops = random.choices([0, 1, 2], weights=[0.35, 0.5, 0.15])[0]
        base = 180 + stops * 90
        offers.append(
            Offer(
                airline=random.choice(AIRLINES),
                price_usd=round(base + random.uniform(-40, 120), 2),
                duration_min=180 + stops * 140 + random.randint(-20, 60),
                stops=stops,
                departs_hour=random.randint(0, 23),
            )
        )
    return offers


def fetch_offers_with_budget(q: ParsedQuery, budget_s: float) -> tuple[list[Offer], bool]:
    """Runs the source search but never exceeds the budget from the caller's
    point of view. A real implementation would pass timeout= to the flight
    API client and catch its timeout exception here."""
    start = time.perf_counter()
    offers = fetch_offers_mock(q)
    elapsed = time.perf_counter() - start
    timed_out = elapsed >= budget_s
    return offers, timed_out


# --------------------------------------------------------------- step 3
def weighted_rank(offers: list[Offer], q: ParsedQuery) -> list[tuple[Offer, float]]:
    """Fast, deterministic ranking. No model call. This alone should produce
    a good result; the model only adjusts for soft preferences (step 4)."""
    if not offers:
        return []
    max_price = max(o.price_usd for o in offers)
    max_dur = max(o.duration_min for o in offers)

    scored = []
    for o in offers:
        price_score = 1 - o.price_usd / max_price
        duration_score = 1 - o.duration_min / max_dur
        stops_score = 1 - o.stops / 2
        redeye_penalty = 0.15 if (q.avoid_red_eyes and (o.departs_hour >= 22 or o.departs_hour <= 5)) else 0.0
        total = 0.45 * price_score + 0.30 * duration_score + 0.25 * stops_score - redeye_penalty
        scored.append((o, total))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


# --------------------------------------------------------------- step 4 (optional)
def soft_rerank(top: list[tuple[Offer, float]], q: ParsedQuery, decide_url: str) -> list[tuple[Offer, float]]:
    """Re-rank the top N with the decision server for preferences that don't
    reduce to a formula ("prefer a good airline"). One batched call."""
    if not q.prefer_good_airline or not decide_url:
        return top

    lines = "\n".join(f"{i}: {o.airline}, ${o.price_usd}, {o.stops} stops" for i, (o, _) in enumerate(top))
    body = {
        "model": "noor-v0",
        "state": lines,
        "questions": {
            "best_index": {
                "type": "choice",
                "instructions": "Considering reputation for service and reliability, which numbered option is the best airline choice?",
                "criteria": {str(i): o.airline for i, (o, _) in enumerate(top)},
            }
        },
    }
    try:
        r = requests.post(f"{decide_url}/v1/decisions", json=body, timeout=1.0)
        r.raise_for_status()
        best_i = int(r.json()["answers"]["best_index"]["choice"])
        # bubble the model's pick to the front, keep the rest of the order
        picked = top[best_i]
        rest = [pair for i, pair in enumerate(top) if i != best_i]
        return [picked] + rest
    except Exception as e:  # never let the soft step break the hard budget
        print(f"  (soft re-rank skipped: {e})", file=sys.stderr)
        return top


# --------------------------------------------------------------- main
def find_best_flight(text: str, use_soft: bool) -> None:
    t0 = time.perf_counter()

    q = parse_query(text)
    t_parsed = time.perf_counter()

    offers, timed_out = fetch_offers_with_budget(q, HARD_TIMEOUT_S)
    t_fetched = time.perf_counter()

    ranked = weighted_rank(offers, q)
    top5 = ranked[:5]
    t_ranked = time.perf_counter()

    if use_soft:
        top5 = soft_rerank(top5, q, DECIDE_URL)
    t_done = time.perf_counter()

    print(f"\nQuery: {text}")
    print(f"Parsed: {q.origin} -> {q.destination} ({q.date_hint}), "
          f"avoid_red_eyes={q.avoid_red_eyes}, prefer_good_airline={q.prefer_good_airline}")
    if timed_out:
        print("  (source search hit the timeout; returning partial results)")

    print(f"\nTop {len(top5)} of {len(offers)} offers:")
    for rank, (o, score) in enumerate(top5, 1):
        print(f"  {rank}. {o.airline:14s} ${o.price_usd:7.2f}  {o.duration_min:3d} min  "
              f"{o.stops} stop(s)  depart {o.departs_hour:02d}:00  score={score:.3f}")

    print(f"\nTiming: parse={1000*(t_parsed-t0):.0f}ms  "
          f"fetch={1000*(t_fetched-t_parsed):.0f}ms  "
          f"rank={1000*(t_ranked-t_fetched):.0f}ms  "
          f"soft_rerank={1000*(t_done-t_ranked):.0f}ms  "
          f"TOTAL={1000*(t_done-t0):.0f}ms (budget {TOTAL_BUDGET_S*1000:.0f}ms)")

    if (t_done - t0) > TOTAL_BUDGET_S:
        print("  ** over budget - tighten the source-search timeout or cache more **")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="flight from DEL to DXB tomorrow, avoid red-eyes")
    ap.add_argument("--soft", action="store_true", help="re-rank top picks with the decide server")
    args = ap.parse_args()
    find_best_flight(args.query, args.soft)
