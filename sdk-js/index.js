"use strict";
/**
 * Browser/Node SDK for the open decision-engine server.
 * Works with any server implementing the /v1/decisions endpoint
 * (this project's server, or Jev-compatible endpoints) — just change baseUrl.
 *
 * Browser safety: pass an origin-locked *publishable* key here, never a
 * secret key. Mint publishable keys server-side with per-key rate limits
 * and spend caps (see the implementation plan, Phase 3b).
 *
 * Usage:
 *   import { DecideClient } from "./index";
 *   const client = new DecideClient({ baseUrl: "http://localhost:8000" });
 *   const { answers } = await client.decide({
 *     state: "I was charged twice, please refund the duplicate.",
 *     questions: {
 *       department: {
 *         type: "choice",
 *         instructions: "Which team should handle this?",
 *         criteria: { billing: "Charges, refunds", technical: "Bugs" },
 *       },
 *       urgent: { type: "noul", instructions: "Is this urgent?" },
 *     },
 *   });
 *   console.log(answers.department.choice, answers.urgent.noul);
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DecideClient = exports.DecideError = void 0;
class DecideError extends Error {
    constructor(message, status) {
        super(message);
        this.name = "DecideError";
        this.status = status;
    }
}
exports.DecideError = DecideError;
class DecideClient {
    constructor(opts) {
        this.baseUrl = opts.baseUrl.replace(/\/$/, "");
        this.apiKey = opts.apiKey;
        this.timeoutMs = opts.timeoutMs ?? 3000;
        this.fetchImpl = opts.fetchImpl ?? fetch;
    }
    async decide(body) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), this.timeoutMs);
        try {
            const res = await this.fetchImpl(`${this.baseUrl}/v1/decisions`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {}),
                },
                body: JSON.stringify({ model: "axiom-v1", ...body }),
                signal: controller.signal,
            });
            if (!res.ok) {
                const text = await res.text().catch(() => "");
                throw new DecideError(`decision request failed: ${res.status} ${text}`, res.status);
            }
            return (await res.json());
        }
        catch (err) {
            if (err?.name === "AbortError") {
                throw new DecideError(`decision request timed out after ${this.timeoutMs}ms`);
            }
            throw err;
        }
        finally {
            clearTimeout(timer);
        }
    }
    /** Convenience: one choice question. */
    async choice(state, instructions, criteria) {
        const { answers } = await this.decide({
            state,
            questions: { q: { type: "choice", instructions, criteria } },
        });
        return answers.q;
    }
    /** Convenience: one yes/no question. Returns probability of "yes". */
    async noul(state, instructions) {
        const { answers } = await this.decide({
            state,
            questions: { q: { type: "noul", instructions } },
        });
        return answers.q.noul;
    }
    /** Convenience: one score question over an ordered rubric. */
    async score(state, instructions, levels) {
        const { answers } = await this.decide({
            state,
            questions: { q: { type: "score", instructions, criteria: levels } },
        });
        return answers.q;
    }
}
exports.DecideClient = DecideClient;
