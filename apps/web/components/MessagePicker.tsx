"use client";

import type { SampleInteraction } from "@/lib/types";

export function MessagePicker({
  interactions,
  selectedId,
  onSelect,
  onClassify,
  busy,
}: {
  interactions: SampleInteraction[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onClassify: () => void;
  busy: boolean;
}) {
  return (
    <div className="card">
      <h2>1. Pick a sample message</h2>
      <p className="hint">
        Every sample here has a recorded replay fixture, so it classifies instantly with no
        Jev key required. Picking a message simulates it arriving at its stated time.
      </p>
      <ul className="message-list">
        {interactions.map((i) => (
          <li
            key={i.id}
            className={`message-item${i.id === selectedId ? " selected" : ""}`}
            onClick={() => onSelect(i.id)}
          >
            <div className="meta">
              {i.channel} · {new Date(i.receivedAt).toLocaleString()}
            </div>
            {i.text}
          </li>
        ))}
      </ul>
      <button className="primary" disabled={!selectedId || busy} onClick={onClassify}>
        {busy ? "Classifying…" : "Classify this message"}
      </button>
    </div>
  );
}
