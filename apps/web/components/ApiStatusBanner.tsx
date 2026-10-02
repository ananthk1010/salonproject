"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";
import type { HealthOut } from "@/lib/types";

/** Polls /api/health until it answers. Render-free-tier cold start means
 * this can take up to ~90s on first load; see architecture doc section 11. */
export function useApiHealth() {
  const [health, setHealth] = useState<HealthOut | null>(null);
  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let attempt = 0;

    async function poll() {
      try {
        const h = await getHealth();
        if (!cancelled) {
          setHealth(h);
          setWaking(false);
        }
      } catch {
        if (cancelled) return;
        attempt += 1;
        if (attempt >= 2) setWaking(true);
        setTimeout(poll, 3000);
      }
    }
    poll();
    return () => {
      cancelled = true;
    };
  }, []);

  return { health, waking };
}

export function ApiStatusBanner({ waking }: { waking: boolean }) {
  if (waking) {
    return (
      <div className="banner">
        Waking the API — Render Free sleeps after 15 minutes idle and takes about a minute to
        come back. This page will update automatically once it responds.
      </div>
    );
  }
  return null;
}

export function ModeBadge({ health }: { health: HealthOut | null }) {
  if (!health) return <span className="badge down">checking…</span>;
  const cls = health.mode === "live" ? "live" : "replay";
  const label = health.mode === "live" ? "LIVE — calling Jev" : "REPLAY — fixtures, no cost";
  return <span className={`badge ${cls}`}>{label}</span>;
}
