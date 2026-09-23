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
export type QuestionType = "choice" | "noul" | "score" | "boolean";
export interface Question {
    type: QuestionType;
    instructions: string;
    criteria?: Record<string, string | null> | string[] | null;
}
export interface DecisionRequestBody {
    model?: string;
    state: string | Record<string, unknown> | unknown[];
    questions: Record<string, Question>;
}
export interface ChoiceAnswer {
    type: "choice";
    choice: string;
    confidence: number;
    probabilities: Record<string, number>;
}
export interface NoulAnswer {
    type: "noul";
    noul: number;
}
export interface ScoreAnswer {
    type: "score";
    score: number;
    confidence: number;
    probabilities: number[];
}
export type Answer = ChoiceAnswer | NoulAnswer | ScoreAnswer;
export interface DecisionResponse {
    model: string;
    answers: Record<string, Answer>;
    usage: {
        input_tokens: number;
        output_tokens: number;
    };
    latency_ms?: number;
}
export interface DecideClientOptions {
    /** e.g. "http://localhost:8000" or your deployed API origin */
    baseUrl: string;
    /** Origin-locked publishable key. Never a secret key in browser code. */
    apiKey?: string;
    /** Abort a call after this many ms. Keep this small for the fast path
     * (see plan Section 2b: 2-5s end-to-end budgets). Default 3000ms. */
    timeoutMs?: number;
    fetchImpl?: typeof fetch;
}
export declare class DecideError extends Error {
    status?: number;
    constructor(message: string, status?: number);
}
export declare class DecideClient {
    private baseUrl;
    private apiKey?;
    private timeoutMs;
    private fetchImpl;
    constructor(opts: DecideClientOptions);
    decide(body: DecisionRequestBody): Promise<DecisionResponse>;
    /** Convenience: one choice question. */
    choice(state: DecisionRequestBody["state"], instructions: string, criteria: Record<string, string | null>): Promise<ChoiceAnswer>;
    /** Convenience: one yes/no question. Returns probability of "yes". */
    noul(state: DecisionRequestBody["state"], instructions: string): Promise<number>;
    /** Convenience: one score question over an ordered rubric. */
    score(state: DecisionRequestBody["state"], instructions: string, levels: string[]): Promise<ScoreAnswer>;
}
