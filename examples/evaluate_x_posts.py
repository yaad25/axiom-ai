"""
Evaluate X Post Options using Axiom AI Decision Engine.
Runs AxiomFastBackend to score which X post copy has the highest viral engagement potential.
"""

import json
from server.model import AxiomFastBackend

post_options = {
    "Option_1_Direct_Benchmark": (
        "Deploying sub-millisecond decision AI just got a lot easier. While typical decision models "
        "(like djev) take ~413 ms per step, Axiom AI evaluates 60 FPS Snake Auto-Pilot moves in < 0.1 ms "
        "on a single CPU core. No GPU required ($0/hr vs $3/hr cloud GPU). Get code, PyPI package, and Docker instructions."
    ),
    "Option_2_Gemma_Style": (
        "Running Axiom AI (axiom-decision-ai) just got a lot easier. You can now spin up an Axiom "
        "API-compatible endpoint locally or on Docker using a single command. Performance is solid: "
        "< 0.1 ms single-step latency and batch execution exceeds 10,000 requests/sec on plain CPU."
    ),
    "Option_3_Punchy_Developer_Hook": (
        "Why wait 413ms for a decision when you can compute probabilities in 0.07ms? Axiom AI is an open-source "
        "typed-decision engine built for real-time control loops, game bots, and sub-millisecond API routers. "
        "Latency: < 0.1 ms (CPU). Cost: $0 (No GPU needed)."
    ),
}

state_prompt = (
    "Evaluate X Twitter launch posts for an open-source sub-1ms AI engine competing against djev. "
    "Select the post that maximizes viral developer engagement, click-through rate, and clear technical benchmark comparison."
)

engine = AxiomFastBackend()

decision = engine.decide(
    state=state_prompt,
    question={
        "type": "choice",
        "instructions": "Pick the highest performing viral X post option",
        "criteria": post_options,
    },
)

print("=" * 60)
print(f"WINNING POST CHOICE: {decision['choice']}")
print(f"CONFIDENCE SCORE:   {decision['confidence'] * 100:.2f}%")
print("PROBABILITY DISTRIBUTION:")
for opt, prob in decision['probabilities'].items():
    print(f"  • {opt}: {prob * 100:.2f}%")
print("=" * 60)
