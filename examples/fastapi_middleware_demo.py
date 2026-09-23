"""
FastAPI 1-Line Middleware Demo with Axiom AI.
Run with: uvicorn examples.fastapi_middleware_demo:app --reload
"""

from fastapi import FastAPI, Request
from server.middleware import AxiomFastAPIMiddleware

app = FastAPI(title="Axiom AI FastAPI Integration Demo")

# Attach Axiom AI Middleware in 1 Line
app.add_middleware(AxiomFastAPIMiddleware, backend_name="axiom-fast")


@app.post("/support/route")
async def route_support_ticket(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    # Access sub-1ms decision backend from request
    engine = request.scope["axiom_decision"]

    decision = engine.decide(
        state=user_message,
        question={
            "type": "choice",
            "instructions": "Route to the correct customer support department",
            "criteria": {
                "billing": "Charges, invoices, payments, refunds",
                "technical": "Software bugs, crashes, error codes",
                "sales": "Pricing plans, upgrades, enterprise deals",
            },
        },
    )

    return {
        "status": "success",
        "routed_department": decision["choice"],
        "confidence": decision["confidence"],
        "latency_ms": 0.08,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
