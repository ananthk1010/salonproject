"use client";

import { useEffect, useState } from "react";
import { ApiError, classifyByInteractionId, getSampleInteractions, getTasks } from "@/lib/api";
import { ApiStatusBanner, ModeBadge, useApiHealth } from "@/components/ApiStatusBanner";
import { MessagePicker } from "@/components/MessagePicker";
import { DecisionPanel } from "@/components/DecisionPanel";
import { TaskBoard } from "@/components/TaskBoard";
import type { ClassifyResponse, SampleInteraction, TaskListItem } from "@/lib/types";

export default function Home() {
  const { health, waking } = useApiHealth();
  const [interactions, setInteractions] = useState<SampleInteraction[]>([]);
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!health) return;
    getSampleInteractions().then(setInteractions).catch(() => undefined);
    refreshTasks();
  }, [health]);

  function refreshTasks() {
    getTasks().then(setTasks).catch(() => undefined);
  }

  async function handleClassify() {
    if (!selectedId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await classifyByInteractionId(selectedId);
      setResult(res);
      refreshTasks();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Something went wrong talking to the API.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <header className="app-header">
        <h1>ABC-Salon — Phase 1</h1>
        <ModeBadge health={health} />
      </header>
      <p className="subtitle">
        Jev (TypeSafe AI) classifies the incoming message. A customer&apos;s tier is a
        deterministic rule, never a Jev question. The only policy is one rule: a booking within
        branch hours is confirmed; everything else is recorded or rejected.
      </p>

      <ApiStatusBanner waking={waking} />
      {error && <div className="error-box">{error}</div>}

      <div className="grid">
        <MessagePicker
          interactions={interactions}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onClassify={handleClassify}
          busy={busy}
        />
        <DecisionPanel result={result} />
      </div>

      <div style={{ marginTop: 20 }}>
        <TaskBoard tasks={tasks} />
      </div>

      <footer className="app-footer">
        Learning and portfolio project. All customer data is synthetic. Not affiliated with any
        salon business. See the{" "}
        <a href="https://github.com/ananthk1010/abc-salon" target="_blank" rel="noreferrer">
          source repository
        </a>{" "}
        for the architecture and whitepaper.
      </footer>
    </div>
  );
}
