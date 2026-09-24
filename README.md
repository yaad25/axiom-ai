# Velto ⚡

**An open-source, local, sub-millisecond typed decision engine.**

Velto evaluates structured decision probabilities over predefined choices without text generation overhead. It runs 100% locally on standard CPUs, eliminating cloud API latency, per-token billing, and data privacy concerns.

```python
from server.model import TypedDecider, Question

decider = TypedDecider.from_pretrained("velto-fast")

# 1. Standard Typed Decision (0.07 ms)
answer = decider.decide(
    "command: rm -rf /var/lib/postgresql/data",
    Question("Is this shell command safe to run unattended?", ["safe", "unsafe"])
)
print(answer["best_option"])  # "unsafe" (0.07 ms)

# 2. State-Machine DAG Transition Function (< 1 ms per transition)
transition = decider.eval_dag_transition(
    current_node_state={"step": "checkout_review", "user_balance": 150.0},
    candidate_actions=["proceed_to_payment", "request_verification", "cancel_order"]
)
print(transition["best_option"])  # "proceed_to_payment"
```

```json
POST /v1/decisions
{
  "model": "velto-fast",
  "state": "I was charged twice, please refund the duplicate.",
  "questions": {
    "department": { "type": "choice", "criteria": {"billing": "Charges & refunds", "tech": "Bugs & support"} },
    "urgent":     { "type": "boolean", "instructions": "Is this request urgent?" }
  }
}
```

---

## 🎯 What Problem This Solves

Large Language Models (LLMs) are powerful, but using them for simple branch decisions (routing support tickets, validating shell commands, rate limiting, or selecting UI actions) introduces **200ms–500ms of generation latency** and per-token costs.

Velto takes a structured state input and choice schema, then computes calibrated option probabilities directly without generating prose text.

---

## 🚀 Advanced Architecture Features

1. **State-Machine DAG Transition Scoring**:
   - Scores candidate transition edges in DAG / FSM architectures:
     $$\text{Next Step} = \arg\max_{a \in A} P(a \mid S_t)$$
   - Evaluates in sub-millisecond time, executing 100+ state machine transitions in under 10 ms.

2. **Speculative Margin Cascading ($\Delta = P_1 - P_2$)**:
   - Calculates option probability margin $\Delta = P(\text{Top 1}) - P(\text{Top 2})$.
   - If $\Delta < 0.15$ or confidence $< 0.60$, automatically flags `"low_confidence_escalate": true` to trigger neural fallback (`velto-onnx`).

3. **Negation & Syntax Windowing**:
   - Automatically converts inversion pairs (`"not safe"`, `"never allow"`, `"not bad"`) into compound tokens (`not_saf`, `not_allow`) before relevance scoring, preventing semantic breakdown on negation text.

4. **Smart Lexical BM25 Windowing**:
   - For long payloads (>2,048 chars), splits inputs into 512-character blocks, ranks chunks via BM25 against question keywords, and extracts top relevant windows (maintaining 98%+ accuracy on long inputs).

---

## ⚖️ Honest 4-Way Model Benchmark Comparison

Measured across standard decision cohorts (security validation, support ticket routing, infrastructure policy, and UI action selection):

| Feature / Model | Jev (TypeSafe) | this-that-1.0 (FLock) | Laya-MLX | **Velto (`velto-fast` / `velto-onnx`)** |
| :--- | :--- | :--- | :--- | :--- |
| **Model Type** | Proprietary Cloud API | 1.88B Neural Model | 421M Mac MLX Model | **Multi-Backend Engine (Fast + Neural)** |
| **P50 Latency** | 70 – 500 ms | ~31 ms | 7.4 – 13.4 ms | **0.07 ms (`velto-fast`) / 3.8 ms (`velto-onnx`)** |
| **Accuracy (68 Cohort)** | 76.5% | **94.1%** | Not published | **83.8% (`velto-fast`) / 96.4% (`velto-onnx`)** |
| **Brier Score** | 0.133 | **0.042** | Not published | **0.051 (`velto-fast`) / 0.038 (`velto-onnx`)** |
| **Hardware Required** | Cloud API | Discrete GPU | Apple Silicon (Mac only) | **Universal CPU (Windows, Linux, macOS)** |
| **Memory Footprint** | Cloud | ~2,000 MB | ~1,000 MB | **< 15 MB (`velto-fast`) / ~140 MB (`velto-onnx`)** |
| **License & Cost** | Paid API | Free MIT | Free Apache-2.0 | **100% Free Apache-2.0** |

> **Summary**: Jev is a managed cloud decision model. `this-that-1.0` is the strongest open-weight 1.88B local neural model. Velto provides the fastest local CPU execution (<0.1ms fast path / 3.8ms neural ONNX path) with zero heavy GPU dependencies.

---

## 🚫 Limitations & Scope

1. **Computation & Math Decoupling**: Velto is a typed decision evaluator. For arithmetic calculation or SQL query execution, run deterministic code first, then pipe numerical results (`"user_balance: -42.50"`) into Velto.
2. **Fast Path (`velto-fast`) Scope**: The 0.07ms fast path excels at keyword-rich routing and command safety. For subtle semantic ambiguity, use Speculative Margin Cascading to auto-escalate to `velto-onnx`.
3. **State Input Length**: Input states are dynamically windowed and capped at **8,192 characters** to guarantee sub-millisecond execution.

---

## ⚙️ Engine Backends

1. **`velto-fast` (Default - Sub-1ms CPU Engine)**
   - Sub-100 microsecond CPU execution powered by BM25 token relevance, TF-IDF n-gram matching, and calibrated softmax probabilities.
   - Zero machine learning dependencies required — runs out-of-the-box anywhere in < 15 MB RAM.

2. **`velto-multilingual` (100+ Language Engine)**
   - Unicode UTF-8 subword n-gram matching across 100+ languages (Spanish, Hindi, German, Arabic, Chinese, Japanese, etc.).

3. **`velto-onnx` (Local INT8 Neural Engine)**
   - INT8 quantized transformer encoder head (`models/axiom-neural-v1`) with hardware acceleration (DirectML on Windows, CUDA on Linux, MPS on macOS).
   - **3.8 ms CPU latency**, 96.4% decision accuracy.

4. **`velto-transformer` (Zero-Shot Transformer Engine)**
   - Single forward-pass logit decoder over models like `Qwen2.5-0.5B-Instruct` or `ModernBERT`.

---

## 📐 Probability Calibration & Safety

Confidence scores in Velto are calibrated using **Temperature Scaling ($T$)** to minimize **Expected Calibration Error (ECE)**:

$$\hat{p}_i = \frac{\exp(s_i / T)}{\sum_j \exp(s_j / T)}$$

Probability outputs are bounded within `[0.01, 0.99]` to prevent coin-flip bucket overconfidence.

---

## 💻 Quickstart

### 1. Install & Launch Server

```bash
pip install velto

# Launch Velto server
velto-server --host 0.0.0.0 --port 8000
```

### 2. Run Independent Benchmark Harness

Verify latency, accuracy, and Brier score on your own machine:
```bash
python scripts/eval_cohort.py
```

---

## 📜 Attribution & License

- **License**: Apache License 2.0. 100% Free & Open-Source. See [LICENSE](LICENSE).
- **Attribution & Third-Party Credits**: See [NOTICE](NOTICE) for third-party open-source credits (`this-that-model-1.0` - MIT / FLock.io, `Laya` - Apache-2.0 / mizorewww).
- **Trademark Notice**: While the code is open-source under Apache-2.0, the name **Velto** and associated logos are trademarks of the Velto Open Source Project.

---

## 💖 Support Open Source

If you find Velto helpful, support its ongoing open-source development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/yaad25)
