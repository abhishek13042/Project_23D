"use client";

import { useEffect, useState } from "react";
import type { Stats } from "@/lib/handlers";

// Loaded in the browser, so /results stays a static page when the database is down (S011-REQ-001)
export function RunStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    fetch("/api/stats")
      .then((response) => (response.ok ? response.json() : null))
      .then(setStats)
      .catch(() => setStats(null));
  }, []);

  if (!stats || stats.total === 0) return null;
  return (
    <section className="prose">
      <h2>Live use</h2>
      <p>
        Visitors have run the model on <span className="num">{stats.total}</span> scans, and{" "}
        <span className="num">{stats.succeeded}</span> finished
        {stats.medianSeconds !== null && (
          <>
            , in a median of <span className="num">{Math.round(stats.medianSeconds)}</span> seconds
          </>
        )}
        . These counts say nothing about accuracy.
      </p>
    </section>
  );
}
