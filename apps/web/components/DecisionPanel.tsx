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

// Jev has exactly three question types. The panel groups answers by type so a
// reader can see all three, and marks which single answer the policy reads.
const GROUPS: { type: Answer["type"]; title: string; blurb: string }[] = [
  {
    type: "choice",
    title: "Choice questions",
    blurb: "Jev picks one option from a list and gives a probability for every option.",
  },
  {
    type: "score",
    title: "Score questions",
    blurb: "Jev places the message on an ordered scale (0 is the lowest level) with a probability for every level.",
  },
  {
    type: "noul",
    title: "Noul (yes/no) questions",
    blurb: "Jev gives the probability that a statement is true. There is no confidence value for these.",
  },
];

export function DecisionPanel({ result }: { result: ClassifyResponse | null }) {
  if (!result) {
    return (
      <div className="card">
        <h2>2. Decision</h2>
        <div className="empty-state">Pick a sample message and classify it to see Jev&apos;s answers here.</div>
      </div>
    );
  }

  const entries = Object.entries(result.answers);

  return (
    <div className="card">
      <h2>2. Decision</h2>
      <p className="hint">
        <span className={`tier-pill ${result.tier}`}>{result.tier}</span>{" "}
        customer tier — computed by a deterministic rule, never by Jev.
      </p>

      <div className={`outcome ${result.action}`}>{OUTCOME_LABEL[result.action]}</div>

      <div className="phase-note">
        <strong>Phase 1 focuses on Intent.</strong> It is the only Jev answer the policy acts on.
        The other five are shown to demonstrate Jev&apos;s three question types and are stored in
        the audit trail.
      </div>

      {GROUPS.map((group) => {
        const items = entries.filter(([, answer]) => answer.type === group.type);
        if (items.length === 0) return null;
        return (
          <section className="answer-group" key={group.type}>
            <h3>{group.title}</h3>
            <p className="group-blurb">{group.blurb}</p>
            {items.map(([id, answer]) => (
              <div key={id}>
                <AnswerRow id={id} answer={answer} />
                {POLICY_RELEVANT.has(id) ? (
                  <p className="row-tag drives">↳ drives Phase 1&apos;s policy</p>
                ) : (
                  <p className="row-tag display">↳ display only, not used by policy</p>
                )}
              </div>
            ))}
          </section>
        );
      })}

      <div className="meta-row">
        <span>mode: {result.mode}</span>
        <span>policy: {result.policyVersion}</span>
        <span>latency: {result.latencyMs.toFixed(0)} ms</span>
        <span>input tokens: {result.inputTokens}</span>
      </div>
    </div>
  );
}
