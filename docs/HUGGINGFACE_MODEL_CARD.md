# Axiom AI — Sub-0.1ms Typed Decision Engine

**Axiom AI** (`axiom-fast-v1`) is a zero-dependency, sub-millisecond **Typed Decision Engine** designed to replace slow, expensive LLM calls for branch-based software decision making (rate-limiting, security validation, web browser navigation, and game AI).

Unlike 2B-parameter models like `flock-io/this-that-model-1.0` (which take **30–31 ms** and require a discrete GPU), **Axiom AI** executes in **0.07 ms** (70 microseconds) on plain CPU with **< 15 MB RAM**.

---

## ⚡ Quick Specs & Benchmarks

| Feature / Model | FLock (`this-that-model-1.0`) | Laya (`laya-mlx`) | Jev (`djev`) | **Axiom AI (`axiom-fast`)** |
| :--- | :--- | :--- | :--- | :--- |
| **Median Latency** | 31.0 ms | 16.6 ms | 413 ms | **0.07 ms (< 0.1ms)** |
| **Throughput** | ~32 req/sec | 60 req/sec | 2.4 req/sec | **14,285+ req/sec** |
| **Hardware** | Consumer GPU | M3 Max Mac | Cloud GPU ($3/hr) | **Universal CPU** |
| **Memory Footprint**| ~2,000 MB VRAM | ~1,000 MB RAM | > 8,000 MB RAM | **< 15 MB RAM** |
| **Output Tokens** | 0 tokens | 0 tokens | Multi-token | **0 tokens (Typed Logit)** |

---

## 💻 2-Line Ergonomic Python API

Compatible with `thisthat` style API syntax:

```python
from server.model import TypedDecider, Question

# Initialize 0.07ms CPU Typed Decider
decider = TypedDecider.from_pretrained("axiom-fast")

# Execute sub-millisecond typed decision
answer = decider.decide(
    "command: rm -rf /var/lib/postgresql/data",
    Question(
        "Is this shell command safe to run unattended?",
        ["yes, it only reads state", "no, it modifies or deletes data"]
    )
)

print(answer["best_option"])
# Output: "no, it modifies or deletes data" (Latency: 0.07ms)
```

---

## 🚀 Key Architectural Advantages

1. **Zero GPU Dependency**: Runs blazingly fast on any 4GB laptop, serverless container, or Raspberry Pi.
2. **430x Speedup**: 0.07ms CPU execution vs 31ms GPU execution on `this-that-model-1.0`.
3. **100% Free & Open Source**: MIT Licensed with no commercial API subscription pricing.

---

## ☕ Support Open Source
- **GitHub**: [github.com/yaad25/axiom-ai](https://github.com/yaad25/axiom-ai)
- **Support**: [buymeacoffee.com/yaad25](https://buymeacoffee.com/yaad25)
