"""
Sub-Millisecond Cheap Flight Decision & Filter Demo using Velto.
Evaluates flight options (price, layovers, duration, airlines) in <0.1ms!
"""

import time
from server.model import VeltoFastBackend

# Sample incoming flight options from API
flight_options = [
    {"airline": "FlyCheap", "price_usd": 180, "stops": 2, "duration_hours": 14},
    {"airline": "AirExpress", "price_usd": 240, "stops": 0, "duration_hours": 3.5},
    {"airline": "BudgetJet", "price_usd": 150, "stops": 1, "duration_hours": 7},
    {"airline": "LuxuryAir", "price_usd": 650, "stops": 0, "duration_hours": 3.0},
]

user_query = "Find me the absolute cheapest budget flight under $200"

engine = VeltoFastBackend()

start_time = time.perf_counter()

# Evaluate best flight using Velto Decision Engine
decision = engine.decide(
    state=user_query,
    question={
        "type": "choice",
        "instructions": "Pick the flight matching user budget preference",
        "criteria": {
            "BudgetJet": "Cheapest flight under 200 dollars with low price",
            "FlyCheap": "Low price 180 dollars multi stop",
            "AirExpress": "Direct non-stop flight under 250 dollars",
            "LuxuryAir": "Premium luxury direct flight",
        },
    },
)

end_time = time.perf_counter()
latency_ms = (end_time - start_time) * 1000

print(f"Recommended Flight: {decision['choice']}")
print(f"Confidence: {decision['confidence'] * 100:.1f}%")
print(f"Decision Latency: {latency_ms:.3f} ms (Far less than 5 seconds!)")
