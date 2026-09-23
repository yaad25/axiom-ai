# Implementation Plan: Typed-Decision API (Jev Alternative)

Prepared 21 Sep 2026. Timeline: about 10 weeks to public launch. Anything marked *(est.)* is an estimate you must verify with your own measurements or current provider pricing.

---

## 0. The product

A hosted API. You send a `state` (text or JSON) plus typed questions (choice, score, yes/no probability). You get typed answers with probabilities and a calibrated confidence, in one fast pass, with no generated prose.

- **Pricing:** $0.039 per 1M input tokens, output free.
- **Competitor:** TypeSafe's Jev is at $0.042/M input, output free, 32K context, currently in beta.
- **The catch:** a price 7% lower is not a reason to switch. Pick one wedge and win it with numbers:
  1. Private / self-hosted / VPC deployment
  2. Best-in-class calibration (trustworthy confidence)
  3. One vertical, fine-tuned (support triage, moderation, agent routing, trading signals)

---

## 1. Architecture (decisions, not options)

**Do not** build a fixed classifier head (for example ModernBERT with Choice/Score/Boolean heads). It can only answer questions it was trained on. Jev-style products accept arbitrary questions at request time.

**Do this instead:**
- Base model: a small decoder, starting with **Qwen2.5-0.5B**, then **1.5B** if accuracy needs it (both Apache-2.0, verify the license before you ship).
- Prompt = `state` + question + criteria/rubric.
- **One forward pass, no generation.** Read the next-token logits over the answer options (labels for choice, levels for score, Yes/No for noul). Softmax gives probabilities. Output is "free" because there is nothing to generate.
- Multiple questions on one state: reuse the state's KV cache (prefix caching) and batch the questions.
- **Calibration:** fit temperature scaling (or isotonic regression) on a held-out set. Report expected calibration error (ECE) per decision type.
- **Rationale** (the "audit" feature) is a separate, optional endpoint. It needs real generation, so it is priced separately and never on the free-output path.

**Hardware reality check:** a 0.5B decoder will not hit 12-25 ms on CPU for 500-token inputs. Plan on a small GPU (L4 / A10 class). CPU-only is realistic only for encoder-style models of roughly 300M parameters or less.

---

## 2. Phases and gates

### Phase 0: Setup and risk removal (Days 1-3)
- [ ] Apply to **Dodo Payments** and **Paddle** now (approvals take time). Describe the product accurately: "typed classification API for developers".
- [ ] Open a **Razorpay** account and finish KYC (for INR / UPI customers).
- [ ] Book a **CA**: GST on exports of services (LUT), foreign inward remittance paperwork, whether you need GST registration / IEC.
- [ ] Get an OpenRouter key and call Jev on 20 real examples to learn its behavior.
- [ ] Send 10 interview requests to developers with routing/triage pain. One question: "what do you use today and what does it cost you?"

### Phase 1: Benchmark before model (Days 4-10)
- [ ] Build **600-1,000 labeled examples**: 3 decision types across 5 domains (support tickets, moderation, agent routing, lead scoring, log triage). Lock 30% as a never-trained-on test set.
- [ ] Write the harness script. It runs Jev (via OpenRouter), a small LLM with structured outputs, and your model, and reports accuracy, macro-F1, ECE, p50/p95 latency, and cost per 1,000 decisions.
- [ ] Read TypeSafe's terms on benchmarking and on using outputs. **Do not train on Jev's outputs.**
- [ ] **Gate A (Day 10):** you know where Jev is strong and weak, and you have chosen your wedge. No wedge, no build.

### Phase 2: Model (Days 10-35)
- [ ] **Data:** 100-300K synthetic examples (varied states, questions, criteria). Label with an open-weight teacher whose license allows training other models. Many hosted-API terms forbid training competing models, so check before using one. Filter by teacher agreement and hand-verify 5-10%.
- [ ] **Train:** LoRA on the 0.5B model first (a few hours on one rented GPU, about $50-150 *(est.)*), evaluate, then try 1.5B.
- [ ] Add score rubrics, yes/no, JSON state, and longer inputs (start at 8K tokens, extend toward 32K).
- [ ] Calibrate on held-out data.
- [ ] **Gate B (Day 35):** within 3 accuracy points of Jev on your test set **and** ECE at or below Jev's on at least 2 of 3 decision types, **or** a clear win in your niche. If not, pivot (see Section 6).

### Phase 3: Serving (Days 30-45)
- [ ] Serve with **vLLM** (prefix caching, continuous batching) or TensorRT/ONNX. Wrap in FastAPI, Docker, TLS.
- [ ] GPU: one L4/A10-class card at about $0.4-0.9/hour *(est.)*, roughly $300-650/month always-on. **Start on serverless GPU** (Modal / RunPod, per-second billing) so fixed cost stays near zero until traffic exists.
- [ ] **Latency target:** match or beat Jev's measured latency. One independent test reported roughly 92-214 ms for Jev; measure it yourself under the same conditions.
- [ ] Endpoint: `POST /v1/decisions` with `state` and typed `questions`, mirroring Jev's request shape where sensible so migration is a base-URL and model-name change.
- [ ] **Metering:** count input tokens with your own tokenizer, log per key, and publish exactly how tokens are counted.

### Phase 3b: Browser support (Days 40-60)
This phase is about **delivering** the product in browsers (SDK and local model). It is not about driving a browser as an agent, which is too slow for the 2-5 s goal (see Section 2b). Two separate things. Ship **A** at launch. Ship **B** as v1.1 (pull it forward only if privacy is your chosen wedge).

**A. Browser SDK and playground (launch)**
- [ ] TypeScript SDK (`decide.choice()`, `decide.score()`, `decide.noul()`) that runs in browsers, Node, and edge runtimes.
- [ ] **Never ship a secret key to the browser.** Issue publishable, origin-locked keys with per-key rate limits and spend caps, or short-lived tokens minted by the customer's backend.
- [ ] Per-key CORS allowlist and request size limits.
- [ ] Web playground: paste a state, add questions, see probabilities live. It doubles as your demo.
- [ ] Later option: a Chrome extension for one-click decisions on selected page text.

**B. In-browser inference (v1.1)**
- [ ] Export to ONNX, quantize (int4/int8), and run with ONNX Runtime Web (WebGPU with WASM fallback) or transformers.js, inside a Web Worker so the UI never blocks.
- [ ] A 0.5B model at 4-bit is roughly a few hundred MB *(est.)*. Cache it in IndexedDB / Cache API, show download progress, load once per device.
- [ ] **Hybrid mode:** run locally when WebGPU and enough memory exist, otherwise fall back to your API automatically.
- [ ] Re-run the full benchmark on the **quantized browser build** and publish that number separately. Quantization costs accuracy.
- [ ] Test on Chrome, Edge, Safari, Firefox, and a mid-range phone. WebGPU support varies, so check current support.
- **Why bother:** data never leaves the device (strong privacy pitch) and each call costs you nothing.
- **The catch:** you cannot meter tokens, and shipped weights can be copied. Sell it as a **license** (per domain or per monthly active user) with terms forbidding extraction.

### Phase 4: Accounts and billing, India-ready (Days 35-55)
- [ ] Auth (GitHub/Google), hashed API keys, usage dashboard, Postgres/Supabase.
- [ ] **Prepaid credits** through Dodo/Paddle: $10 minimum top-up, optional auto-top-up. Keep a ledger in your DB and decrement per request. Prepaid avoids fixed per-charge fees eating small bills.
- [ ] **Razorpay** for Indian customers (UPI and INR cards).
- [ ] The merchant of record handles global VAT/sales tax. Your CA handles the Indian side.
- [ ] Docs: one-page quickstart (curl, Python, JS), a playground, a status page.
- [ ] ToS and privacy policy. Selling point: **no training on customer data by default.**
- [ ] Free tier: 2M input tokens on signup (about $0.08 at list price).

### Phase 5: Launch (Days 55-70)
- [ ] Open-source the **benchmark harness and results**, including the cases where you lose. Honest numbers earn trust on Hacker News.
- [ ] Post to Show HN, r/LocalLLaMA, and X. Claim only what you measured.
- [ ] Onboard **5 design partners** free for 60 days in exchange for feedback and a case study.
- [ ] Personally reach out to anyone who burns through the free tier.
- [ ] Pursue listings on model aggregators (OpenRouter-style marketplaces) once stable.

---

## 2b. Reference use case: "best flight from A to B in 2-5 seconds"

**Rule: no browser on the critical path.** Driving a real browser (headless Chrome plus an agent) typically takes 10-60+ seconds *(est.)* and breaks on CAPTCHAs, bot blocks, and layout changes. A direct API call is the only reliable way to hit 2-5 s.

**Latency budget** *(est., measure it)*

| Step | Time |
|---|---|
| Parse the request ("Delhi to Dubai Friday") | 20-100 ms (rules or your model) |
| Resolve airports and dates | under 10 ms (local airport table) |
| Flight-data API search | 1-4 s (the bottleneck) |
| Rank offers with your model | 20-100 ms for 50-200 offers in one batch |
| Format and return | under 50 ms |
| **Total** | **about 1.5-4.5 s** |

**How to hit it**
- **Data source:** you need a flight API with instant self-serve access. **Duffel** is the practical pick (instant signup, usage-based pricing). Amadeus Self-Service shut down on July 17, 2026. Kiwi Tequila and Skyscanner are application-based, and Sabre/Travelport are enterprise-only.
- Set a **hard search timeout (about 3 s)** and return whatever has arrived. Duffel has a supplier-timeout setting, so verify it in their docs.
- Search in parallel (nearby airports, plus or minus one day) but respect rate limits. One Duffel integration guide lists 60 requests per 60 seconds, so verify the current limit.
- **Cache** route-and-date results for 5-10 minutes. Cache hits return in under 100 ms.
- **Stream results:** show the first offers at about 2 s and refine as slower suppliers respond.
- **Rank in one batch:** one shared preferences prefix, then one short line per offer (about 60 tokens each). 100 offers is about 6K tokens, roughly $0.00023 at $0.039/M.
- Start with a **weighted formula** (price, duration, stops, layover, departure time). Use the model only for soft preferences ("avoid red-eyes", "prefer a good airline") so ranking never becomes the slow part.
- Use browser automation only as an **async background check** or for sites with no API, never in the 2-5 s path.

**What you need:** one flight API key, a small server, and your tiny ranking model. No browser fleet.

---

## 3. Pricing

| Tier | Price | Notes |
|---|---|---|
| Public API | $0.039/M input, output free | Parity price with Jev's $0.042/M. Prepaid credits, $10 minimum. |
| Volume | Discount above roughly $500/month commit | Only after you have data on real usage. |
| Dedicated instance | Flat monthly, start around $299-999 *(est.)* | Private, SLA, no noisy neighbors. This is where the margin is. |
| On-prem / VPC license | Custom | Quote from real conversations. Do not set a list price yet. |
| Rationale add-on | Separate per-token price | Generation costs real compute. |
| Browser local license | Per domain or per MAU, custom *(est.)* | No token metering is possible, so sell it as a license. Free for localhost/dev. |

Reality check: at $0.039/M, **$1,000 MRR from the public API needs about 25.6B input tokens per month**. Dedicated and on-prem tiers are where real revenue comes from.

---

## 4. Unit economics *(est., verify)*

- An always-on GPU costs about $300-650/month, so the public API alone needs about **8-17B tokens/month** to cover it.
- Margin depends almost entirely on utilization. It is poor at low volume and can reach 85%+ at high utilization. Serverless GPU keeps early costs low.
- MoR fees (about 5% + $0.50 per charge) hurt small bills. Prepaid credits fix most of it.
- Measure your real tokens/second per GPU before committing to a price floor.

---

## 5. Budget to launch *(est.)*

| Item | Cost |
|---|---|
| Training GPU time | $100-400 |
| Data generation / teacher compute | $0-300 |
| Eval labeling (self or freelancers) | $0-200 |
| Serving, first 2 months | $100-1,000 (serverless vs always-on) |
| Domain, email, misc | about $50 |
| CA consult | a few thousand rupees to start |
| **Total** | **about $500-2,000** |

---

## 6. Kill and pivot criteria (write these down now)

| When | Trigger | Action |
|---|---|---|
| Day 10 | Interviews show no pain, or you cannot label 500 examples | Stop or change niche |
| Day 35 | Gate B failed | Pivot to a niche fine-tuned model, or open-source the model and sell hosting |
| Day 55 | Latency worse than Jev's, or margin under 40% at expected volume | Fix serving before launching |
| Day 100 | Fewer than 3 customers paying $20+/month and fewer than 10 active free users | Shrink to a niche or open-source project. Do not raise money |
| Any time | TypeSafe cuts price 50%+ | Shift focus to dedicated and on-prem tiers |
| After the v1.1 browser build | Quantized build loses more than 3 points vs the server model, or first download is over about 500 MB | Ship the API-backed browser SDK only and skip local inference |

---

## 7. Risks

- **Price war:** TypeSafe can cut prices at will. Mitigation: private deployment, niche accuracy.
- **Beta competitor:** Jev's behavior and pricing may change. Re-run your benchmark monthly.
- **Legal:** teacher-model terms, base-model licenses, benchmark terms, MoR approval, Indian export compliance. Review each before launch.
- **Claims:** publish only measured numbers, with failing cases included.
- **Reliability:** a status page and an SLA matter more than a small price edge.
- **Browser inference:** weights can be extracted, WebGPU support is uneven, and mobile memory is tight. Mitigate with license terms, automatic fallback to the API, and honest device requirements.

---

## 8. First 72 hours

1. Apply to Dodo Payments and Paddle. Open Razorpay.
2. Book a CA appointment.
3. Get an OpenRouter key and run 20 examples through Jev.
4. Send 10 developer interview requests.
5. Start the benchmark spreadsheet (state / question / type / correct label).
