#!/usr/bin/env python3
"""
Verify LayaBackend on a machine with real internet access.

This was NOT run inside the dev sandbox that generated this repo — that
container has no network route to huggingface.co, so the LayaBackend code
in server/model.py is written correctly against the documented API but is
UNTESTED against real weights. Run this script yourself before trusting it.

    pip install laya
    python scripts/verify_laya.py

Expected: downloads ~1.7GB on first run, then prints a decision, a latency
number, and a warning if you're running on CPU (Laya's published numbers
are GPU numbers; CPU will be much slower).
"""
import sys
import time


def main():
    try:
        import laya
    except ImportError:
        sys.exit("Install first: pip install laya")

    print("Loading convaiinnovations/laya (downloads on first run)...")
    t0 = time.perf_counter()
    agent = laya.load("convaiinnovations/laya")
    print(f"Loaded in {time.perf_counter() - t0:.1f}s")

    try:
        import torch
        if torch.cuda.is_available():
            device = f"cuda ({torch.cuda.get_device_name(0)})"
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            device = "mps (Apple Silicon)"
        else:
            device = "cpu"
    except ImportError:
        device = "unknown (torch not importable)"
    print(f"Detected device: {device}")
    if device == "cpu":
        print("WARNING: running on CPU. Expect much higher latency than the")
        print("32.8ms p50 GPU number below — this is fine for correctness")
        print("testing, not for a latency claim.")

    state = "I was billed twice. Please refund the duplicate charge today."
    questions = {
        "department": {
            "type": "choice",
            "instructions": "Which team should handle this?",
            "criteria": {
                "billing": "invoices, payments, refunds",
                "technical": "bugs and outages",
                "sales": "new purchases",
            },
        },
        "refund": {
            "type": "noul",
            "instructions": "Does the customer ask for money back?",
        },
    }

    # Warm-up call (excluded from the timed measurement; first call pays for
    # lazy init / kernel compilation and isn't representative of steady state)
    agent.predict(state, questions)

    n = 20
    t0 = time.perf_counter()
    for _ in range(n):
        result = agent.predict(state, questions)
    elapsed_ms = (time.perf_counter() - t0) * 1000 / n

    print("\nAnswers:", result["answers"])
    print(f"\nAvg latency over {n} calls: {elapsed_ms:.1f}ms")
    print("(Convai's published p50 on a Tesla T4 GPU is 32.8ms. If you're on")
    print(" CPU or a weaker GPU, expect a much higher number than that.)")

    # Zero-shot accuracy warning per the model card
    print("\nReminder: this checkpoint's zero-shot accuracy is reported at")
    print("~0.362 (barely above a 0.318 random baseline). Don't trust its")
    print("answers on your real task until you've fine-tuned or at least")
    print("evaluated it on your own labeled examples (see examples/bench.py).")


if __name__ == "__main__":
    main()
