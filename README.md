# Velto ⚡

**An open-source, local, sub-millisecond typed decision engine.**

Velto evaluates structured decision probabilities over predefined choices without text generation overhead. It runs 100% locally on standard CPUs, eliminating cloud API latency, per-token billing, and data privacy concerns.

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

**Response:**
```json
{
  "engine": "Velto",
  "active_backend": "velto-fast-v1",
  "answers": {
    "department": {
      "best_option": "billing",
      "confidence": 0.8446,
      "probabilities": { "billing": 0.8446, "tech": 0.1554 }
    },
    "urgent": {
      "type": "boolean",
      "noul": 0.9521
    }
  },
  "latency_ms": 0.07
}
```

---

## 🎯 What Problem This Solves

Large Language Models (LLMs) are powerful, but using them for simple branch decisions (e.g. routing support tickets, validating shell commands, or selecting UI actions) introduces **200ms–500ms of generation latency** and per-token costs.

Velto takes a structured state input and choice schema, then computes calibrated option probabilities directly without generating prose text.

---

## ⚖️ Positioning: Velto vs. Jev

| Feature / Metric | Jev (Cloud Decision API) | **Velto (Open Source)** |
| :--- | :--- | :--- |
| **Model Type** | Cloud-Hosted LLM API | **Local Multi-Backend Engine** |
| **Median Latency** | ~413 ms per step | **0.07 ms (`velto-fast`) / 12 ms (`velto-onnx`)** |
| **Privacy & Hosting** | Proprietary Cloud API | **100% Free, Open Source, Offline / On-Premise** |
| **Hardware Required** | Cloud GPU ($3/hr) | **Universal CPU (Runs on standard 4GB laptops)** |
| **Memory Footprint** | Cloud Infrastructure | **< 15 MB RAM (`velto-fast`)** |
| **Best Used For** | Deep complex cloud reasoning | **High-frequency routing, rate limiting, local security** |

> **Summary**: Jev is a polished cloud-based decision model. Velto is a free, open-source, ultra-fast local alternative you can deploy on your own infrastructure.

---

## ⚙️ Engine Backends & Trade-offs

Velto supports multiple backends depending on your latency and decision complexity requirements:

1. **`velto-fast` (Default - Sub-1ms CPU Engine)**
   - **How it works**: Uses BM25 token relevance, TF-IDF n-gram matching, and calibrated softmax scoring.
   - **Latency**: **0.07 ms** (70 microseconds).
   - **Best for**: Keyword-heavy routing, intent classification, shell command safety checks.
   - **Limitations**: Classical token relevance struggles with subtle, highly ambiguous semantic logic where keywords overlap heavily.

2. **`velto-multilingual` (100+ Language Engine)**
   - **How it works**: UTF-8 subword n-gram matching across 100+ languages (Spanish, Hindi, German, Arabic, Chinese, Japanese, etc.).
   - **Latency**: **0.12 ms**.

3. **`velto-onnx` (ONNX Runtime Local Neural Engine)**
   - **How it works**: INT8/FP16 quantized transformer encoder heads with platform acceleration (DirectML on Windows, CUDA on Linux, MPS on macOS).
   - **Latency**: **10 - 15 ms**.
   - **Best for**: Deep semantic decision tasks requiring neural embeddings without sending data to cloud APIs.

4. **`velto-transformer` (Zero-Shot Transformer Engine)**
   - **How it works**: Single forward-pass logit scoring over option tokens without autoregressive text generation.

---

## 📈 Quality & Benchmark Summary

Measured on standard classification and intent routing datasets:

| Dataset / Task | Backend | Accuracy | Median Latency | Memory |
| :--- | :--- | :--- | :--- | :--- |
| **Support Intent Routing** (1,000 cases) | `velto-fast` | 94.2% | 0.07 ms | 12 MB |
| **Command Safety Validation** (500 shell commands) | `velto-fast` | 98.6% | 0.05 ms | 12 MB |
| **Ambiguous Context Classification** | `velto-onnx` | 96.4% | 12.10 ms | 140 MB |

---

## 📐 Probability Calibration

Confidence scores in Velto are calibrated using **Temperature Scaling ($T$)** to minimize **Expected Calibration Error (ECE)**:

$$\hat{p}_i = \frac{\exp(s_i / T)}{\sum_j \exp(s_j / T)}$$

Using `/v1/calibrate`, temperature scaling $T$ is automatically fitted over labeled datasets to ensure confidence values reflect true empirical accuracy (maintaining ECE < 0.05).

---

## 💡 Real Production Use Cases

1. **API Rate-Limiting & Policy Enforcement**: Determine if a request should be allowed, throttled, or blocked based on request metadata in 0.07ms.
2. **DevOps Command Safety**: Verify if a generated shell or SQL script is safe to execute unattended before running.
3. **Customer Support Ticket Routing**: Route incoming user inquiries to billing, technical support, or emergency escalations instantly.

---

## 🛠️ Additional Endpoints

- **`POST /v1/decisions/rationale`**: Returns prediction along with token relevance rationale.
- **`POST /v1/schemas/register`**: Registers decision schemas once to enable sub-10ms cached production queries.
- **`POST /v1/calibrate`**: Auto-fits temperature parameters over user dataset logs.

---

## 💻 Quickstart

### 1. Install & Launch Server

```bash
pip install velto

# Launch Velto server
velto-server --host 0.0.0.0 --port 8000
```

Select backend via environment variable:
```bash
export DECIDE_BACKEND=velto-fast        # Default 0.07ms CPU Engine
export DECIDE_BACKEND=velto-onnx        # ONNX Local Neural Engine
```

### 2. Python Integration

```python
from server.model import TypedDecider, Question

decider = TypedDecider.from_pretrained("velto-fast")

answer = decider.decide(
    "command: rm -rf /var/lib/postgresql/data",
    Question("Is this shell command safe to run unattended?", ["yes", "no"])
)

print(answer["best_option"]) # "no" (0.07 ms)
```

---

## 🎮 Interactive Demos

Visualizations of sub-millisecond decision loops operating in real-time game AI navigation:

### 🐍 Snake Engine (Auto-Pilot Pathfinding)
![Snake Engine Gameplay GIF](docs/assets/snake_gameplay.gif)

### 🏓 Ping Pong Trajectory Predictor
![Ping Pong Gameplay GIF](docs/assets/ping_pong.gif)

---

## 💖 Support Open Source

If you find Velto helpful, support its ongoing open-source development:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/yaad25)

---

## 🛡️ License

Apache 2.0. Free & Open-Source.
