// Hand-written to mirror apps/api/app/schemas and app/jev/answers.py.
// The authoritative contract is packages/contracts/openapi.json, generated
// by `make contract`; these types are kept in sync manually for now. CI's
// contract check (openapi diff) is what catches real drift.

export type ChoiceAnswer = {
  type: "choice";
  choice: string;
  probabilities: Record<string, number>;
  confidence: number;
  confidence_is_fallback: boolean;
};

export type ScoreAnswer = {
  type: "score";
  score: number;
  probabilities: Record<string, number>;
  confidence: number;
  confidence_is_fallback: boolean;
};

export type NoulAnswer = {
  type: "noul";
  noul: number;
};

export type Answer = ChoiceAnswer | ScoreAnswer | NoulAnswer;

export type Action = "confirmed" | "rejected_outside_hours" | "recorded";

export type TaskOut = {
  type: "booking_request";
  status: "confirmed";
};

export type ClassifyResponse = {
  decisionId: string;
  interactionId: string | null;
  customerId: string | null;
  tier: string;
  answers: Record<string, Answer>;
  confidenceMap: Record<string, number>;
  action: Action;
  task: TaskOut | null;
  policyVersion: string;
  mode: "live" | "replay";
  route: string;
  latencyMs: number;
  inputTokens: number;
};

export type SampleInteraction = {
  id: string;
  customerId: string;
  branchId: string;
  channel: "phone_note" | "web_form" | "whatsapp_mock";
  text: string;
  receivedAt: string;
};

export type CustomerOut = {
  id: string;
  displayName: string;
  branchId: string;
  joinedOn: string;
  tier: string;
  lastSpend: number | null;
};

export type TaskListItem = {
  decisionId: string;
  interactionId: string | null;
  customerId: string | null;
  type: string;
  status: string;
  createdAt: string;
};

export type HealthOut = {
  status: "ok";
  mode: "live" | "replay" | "auto";
  route: string;
  budgetRemainingTokens: number;
  policyVersion: string;
  version: string;
};

export const QUESTION_LABELS: Record<string, string> = {
  intent: "Intent",
  service_category: "Service category",
  urgency: "Urgency",
  frustration: "Frustration",
  wants_specific_stylist: "Wants a specific stylist",
  wants_callback: "Wants a callback",
};
