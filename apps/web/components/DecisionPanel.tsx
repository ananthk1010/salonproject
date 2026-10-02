"use client";

import type { Answer, ClassifyResponse } from "@/lib/types";
import { QUESTION_LABELS } from "@/lib/types";

const OUTCOME_LABEL: Record<ClassifyResponse["action"], string> = {
  confirmed: "Confirmed — booking task created",
  rejected_outside_hours: "Rejected — outside branch hours",
  recorded: "Recorded — classified, no task (not a booking)",
};

function ProbabilityBars({ probabilities, top }: { probabilities: Record<string, number>; top: string }) {
  const entries = Object.entries(probabilities).sort((a, b) => b[1] - a[1]);
  return (
    <div className="prob-bars">
      {entries.map(([label, p]) => (
        <div className="prob-bar-track" key={label}>
          <div className="prob-bar-label">{label}</div>
          <div className="prob-bar-bg">
            <div
              className={`prob-bar-fill${label === top ? " top" : ""}`}
              style={{ width: `${Math.round(p * 100)}%` }}
            />
          </div>
          <div className="prob-bar-pct">{Math.round(p * 100)}%</div>
        </div>
      ))}
    </div>
  );
}

function AnswerRow({ id, answer }: { id: string; answer: Answer }) {
  const label = QUESTION_LABELS[id] ?? id;
  if (answer.type === "noul") {
    const pct = Math.round(answer.noul * 100);
    return (
      <div className="answer-row">
        <div className="q-label">
          <span>{label}</span>
        </div>
        <div className="noul-value">{pct}% likely{pct >= 50 ? " — yes" : ""}</div>
      </div>
    );
  }
  const confPct = Math.round(answer.confidence * 100);
  const top = answer.type === "choice" ? answer.choice : String(Math.round(answer.score));
  return (
    <div className="answer-row">
      <div className="q-label">
        <span>{label}</span>
        <span className="conf">
          confidence {confPct}%{answer.confidence_is_fallback ? " (computed)" : ""}
        </span>
      </div>
      <ProbabilityBars probabilities={answer.probabilities} top={top} />
    </div>
  );
}

const POLICY_RELEVANT = new Set(["intent"]);

export function DecisionPanel({ result }: { result: ClassifyResponse | null }) {
  if (!result) {
    return (
      <div className="card">
        <h2>2. Decision</h2>
        <div className="empty-state">Pick a sample message and classify it to see Jev&apos;s answers here.</div>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>2. Decision</h2>
      <p className="hint">
        <span className={`tier-pill ${result.tier}`}>{result.tier}</span>{" "}
        customer tier — computed by a deterministic rule, never by Jev.
      </p>
      <div className={`outcome ${result.action}`}>{OUTCOME_LABEL[result.action]}</div>

      {Object.entries(result.answers).map(([id, answer]) => (
        <div key={id} style={{ opacity: POLICY_RELEVANT.has(id) ? 1 : 0.85 }}>
          <AnswerRow id={id} answer={answer} />
          {POLICY_RELEVANT.has(id) && (
            <p style={{ marginTop: -8, marginBottom: 12, fontSize: 11, color: "#2f8f4e" }}>
              ↳ this is the only answer Phase 1&apos;s policy reads
            </p>
          )}
        </div>
      ))}

      <div className="meta-row">
        <span>mode: {result.mode}</span>
        <span>policy: {result.policyVersion}</span>
        <span>latency: {result.latencyMs.toFixed(0)} ms</span>
        <span>input tokens: {result.inputTokens}</span>
      </div>
    </div>
  );
}
