# The Sub-70ms Plan: Fast-Path Decision Engine

Companion to [`implementation-plan.md`](implementation-plan.md). That plan covers the full product (arbitrary questions, browser support, billing, launch). This plan is narrower: **how to get p95 latency under 70ms**, which the original decoder-based architecture cannot reliably do. Anything marked *(est.)* needs verification with your own measurements.

---

## 1. The core trade-off — read this before building anything

Jev-style products (arbitrary questions, sent fresh each request) need a **decoder** model that reads your question at request time. That's flexible but slow: 50-100ms+ even for TypeSafe's own optimized model, and 200ms+ realistically once you count network round-trip.

To get comfortably under 70ms, you give up per-request flexibility and use an **encoder** with a **fixed classification head**, defined once per customer at onboarding, not re-specified every call.

| | Decoder (arbitrary questions) | Encoder (fixed schema) |
|---|---|---|
| Flexibility | New question every request | Question set fixed at onboarding |
| Speed (GPU, INT8) | 50-100ms+ *(est.)* | 8-20ms *(est.)* |
| Matches Jev's product | Yes | No — different product shape |
| Matches your <70ms goal | Risky, little margin | Comfortable margin |

**Decision: build the encoder path.** It's a different product than Jev, not a clone — pitch it as "define your decision schema once, then get sub-20ms typed answers forever," instead of "ask us anything." This is also a legitimate, defensible wedge (Section 6 of the main plan lists exactly this kind of specialization as a real differentiator).

If a customer later needs true arbitrary questions, route those calls to a decoder fallback (the `TransformerBackend` already in the repo) and be upfront that fallback is slower.

---

## 2. Latency budget (target: 70ms p95, end to end)

| Stage | Budget | Notes |
|---|---|---|
| Client → server network | 5-15ms | Same-region deploy, HTTP keep-alive, no per-request TLS handshake |
| Auth + request parsing | under 1ms | Trivial |
| Tokenization | 1-3ms | Fast tokenizers (Rust-backed) only |
| **Model forward pass** | **8-20ms** | The whole plan below is about hitting this number |
| Softmax + response formatting | under 1ms | Trivial |
| Response → client network | 5-15ms | Same as above |
| **Total** | **~20-55ms**, leaving 15-50ms margin under 70ms | Margin absorbs p95 variance, GC pauses, network jitter |

Build in margin, don't design to exactly 70ms — p95 (not average) is the number that matters, and tail latency is always worse than your median tests suggest.

---

## 3. Model architecture

### 3.1 Base model
- **ModernBERT-base (149M params)**, released 2024/2025, Apache-2.0. Faster and more accurate than older BERT variants at a similar size, and specifically designed for efficient inference.
- Fallback if you need it smaller: a distilled encoder (DistilBERT-class, ~66M params) — faster, some accuracy cost. Only drop to this if ModernBERT-base doesn't hit budget on your hardware.

### 3.2 Heads (per decision type)
- **Choice:** a linear classification head over N labels, softmax output.
- **Noul (yes/no):** a single sigmoid output, or 2-class softmax (equivalent, pick one for consistency).
- **Score:** an ordinal head over the rubric levels (K-1 sigmoid thresholds, or plain K-way softmax — start with softmax, it's simpler and Section 5's calibration step handles the rest).

### 3.3 Schema definition (replaces per-request `criteria`)
At onboarding, a customer defines their question set once:
```json
{
  "customer_id": "acme_support",
  "questions": {
    "department": {"type": "choice", "labels": ["billing", "technical", "account", "other"]},
    "urgent": {"type": "noul"},
    "severity": {"type": "score", "levels": ["cosmetic", "workaround exists", "blocking"]}
  }
}
```
This becomes a small multi-head model (or LoRA adapter) trained/fine-tuned specifically for that schema. Each customer gets their own head(s) on a shared base encoder — cheap to add, fast to swap.

---

## 4. Serving stack

1. **Export to ONNX**, quantize to **INT8** (dynamic or static quantization — static needs a calibration dataset but is faster; start with dynamic, move to static once you have real traffic data). INT8 typically halves inference time versus FP16/FP32.
2. **Runtime: ONNX Runtime** with the CUDA execution provider (or TensorRT for more speed, more setup effort). Skip raw PyTorch in production — it's slower and heavier than it needs to be for a fixed-shape encoder.
3. **Hardware: GPU required for the <70ms target.** An L4 or A10-class card. INT8 ModernBERT-base on GPU is roughly 8-15ms *(est.)* for typical input lengths (under 512 tokens); the same on CPU is 40-80ms *(est.)*, which eats your whole budget by itself. **CPU-only cannot reliably hit 70ms — don't try.**
4. **No cold starts.** Always-on instance, not serverless-per-request. Serverless cold starts (model load, CUDA init) can add hundreds of milliseconds to several seconds — acceptable for the public token-priced API in the main plan, not acceptable here.
5. **Micro-batching, capped.** If concurrent requests arrive, batch them, but cap the wait at 2-3ms before dispatching whatever you have. Don't let batching logic itself add latency to a lone request.
6. **Keep-alive everywhere.** Persistent connections from client to server, and from your server to the GPU worker process, so you're not paying TCP/TLS setup cost per call.
7. **Co-locate.** API gateway and GPU worker in the same region/VPC — every network hop you remove is milliseconds back.

---

## 5. Training and calibration

1. **Per-customer fine-tuning data:** 200-1,000 labeled examples per schema *(est.)* — far less than the general-purpose model in the main plan needed, because the task is narrow and fixed.
2. **Fine-tune method:** full fine-tune of the small heads is cheap; if you're sharing one base encoder across many customers, use LoRA adapters per customer instead of full fine-tunes, so you're not storing a full 149M-parameter copy per customer.
3. **Calibrate** with temperature scaling on a held-out split, same as the main plan (Section 1). Publish expected calibration error (ECE) per customer schema — a false "0.9 confidence" is worse than no confidence at all.
4. **Re-run `bench.py`** (already in your repo) against the encoder build once it's trained, and report accuracy **and** latency in the same table, since a faster model that's meaningfully less accurate isn't automatically a win — quantify the trade.

---

## 6. Build order and milestones

| Phase | Days | Deliverable | Gate |
|---|---|---|---|
| 1. Prototype | 1-3 | ModernBERT-base + one fixed schema, FP32, no quant | Runs end to end, correctness only |
| 2. Quantize + serve | 4-7 | ONNX INT8, ONNX Runtime, on a rented GPU | **Measure p50/p95 latency for real — this is the checkpoint that validates or kills the <70ms target** |
| 3. Multi-schema | 8-12 | LoRA-per-customer or multi-head setup | Two schemas served from one deployment without latency regression |
| 4. Calibration + eval | 13-16 | Temperature scaling, ECE reported, `bench.py` run | Accuracy documented against the general decoder build |
| 5. Production hardening | 17-21 | Keep-alive, co-location, capped micro-batching, monitoring | p95 under 70ms sustained under realistic concurrent load, not just single-request tests |

**Gate at Phase 2 is the one that matters most.** If INT8 ModernBERT-base on your actual GPU doesn't come in under ~20ms for real inputs, stop and re-plan before building the rest — everything downstream assumes that number holds.

---

## 7. What I can build next in this container

I can implement `EncoderBackend` in your existing `server/model.py` (ModernBERT-base, ONNX INT8) and get you a **real measured latency number** on the hardware available here, rather than the estimates above. Container GPU availability varies, so if there's no GPU here, I'll benchmark on CPU and extrapolate honestly rather than claim a number I haven't measured.

Say the word and I'll build and benchmark it now.

---

## 8. Risks specific to this path

- **You're no longer building "Jev, cheaper."** You're building a different product (fixed-schema, ultra-low-latency). Market it as that, not as a drop-in Jev replacement — a prospect who needs arbitrary per-request questions will bounce off this.
- **Per-customer onboarding friction.** Defining a schema upfront is a heavier sales motion than "sign up and call the API." Worth it for the latency win, but plan the onboarding flow.
- **INT8 accuracy loss.** Quantization can cost a few points of accuracy — measure it, don't assume it's free.
- **p95 under real concurrent load is a different number than p50 on an idle GPU.** Load-test before publishing any latency claim.
