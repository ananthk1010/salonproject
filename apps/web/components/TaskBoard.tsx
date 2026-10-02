"use client";

import type { TaskListItem } from "@/lib/types";

export function TaskBoard({ tasks }: { tasks: TaskListItem[] }) {
  return (
    <div className="card">
      <h2>3. Confirmed bookings</h2>
      <p className="hint">
        The only task type Phase 1 creates. Everything else (price enquiries, complaints,
        rejected bookings) is classified and audited but never shows up here.
      </p>
      {tasks.length === 0 ? (
        <div className="empty-state">No confirmed bookings yet this session.</div>
      ) : (
        <table className="task-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th>Type</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.decisionId}>
                <td>{t.customerId ?? "—"}</td>
                <td>{t.type}</td>
                <td>{t.status}</td>
                <td>{new Date(t.createdAt).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
