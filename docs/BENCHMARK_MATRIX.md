# Technical Comparison: this-that-model-1.0 vs Axiom AI

A technical side-by-side analysis of **FLock's `this-that-model-1.0`** and **`Axiom AI`**.

---

## 📊 Feature & Performance Matrix

| Metric / Aspect | FLock (`this-that-model-1.0`) | **Axiom AI (`axiom-fast` & `axiom-onnx`)** |
| :--- | :--- | :--- |
| **Core Technology** | 1.88B Neural Model (Hybrid DeltaNet + Attention) | **Multi-Backend Engine** (Classical IR + Quantized ONNX + Transformer) |
| **P50 Latency** | ~31.0 ms (Consumer GPU) | **0.07 ms (`axiom-fast` CPU) / 12.0 ms (`axiom-onnx`)** |
| **Hardware Required** | Discrete GPU / Apple MPS (2GB VRAM) | **Universal CPU** (Runs on standard 4GB laptops, Raspberry Pi, serverless) |
| **RAM Footprint** | ~2,000 MB VRAM / RAM | **< 15 MB RAM** (`axiom-fast`) / **~140 MB** (`axiom-onnx`) |
| **Multilingual Reach** | Primary English Focus | **100+ Languages** (`axiom-multilingual` Unicode n-grams) |
| **Platform Support** | CUDA, MPS, PyTorch runtime | **Windows DirectML, Linux CUDA/ROCm, macOS MPS, CPU Everywhere** |
| **Integration** | `thisthat` Python SDK | **PyPI package (`axiom-decision-ai`), FastAPI/Flask Middlewares, JS/TS SDK** |
| **License** | MIT | **Apache 2.0 (100% Free & Self-Hostable)** |

---

## 🎯 Architectural Selection Guide

### Choose `this-that-model-1.0` when:
- You need a dedicated **1.88B neural decision model** trained specifically for complex multi-step reasoning.
- You have a discrete GPU or Apple Silicon Mac available and can allocate **~30 ms per step**.

### Choose `Axiom AI` when:
- You require **sub-millisecond execution (< 0.1 ms)** for high-frequency routing, game AI, rate-limiting, or security checks.
- You need **zero heavy dependencies**, zero GPU cost, and a light footprint (**< 15 MB RAM**).
- You want 1-line **FastAPI / Flask middleware** integration into existing web APIs.
