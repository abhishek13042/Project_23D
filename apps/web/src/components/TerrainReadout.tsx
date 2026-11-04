"use client";

import { useState, type FocusEvent, type PointerEvent, type ReactNode } from "react";
import { caseLabel, ml } from "@/lib/results";

type Reading = { id: string; score: string; tumor: string; kidney: string; open: boolean };

function readSpot(target: EventTarget): Reading | null {
  const spot = (target as Element).closest<SVGElement>("[data-case]");
  if (!spot) return null;
  const { case: id, score, tumor, kidney, open } = spot.dataset;
  return { id: id!, score: score!, tumor: tumor!, kidney: kidney!, open: open === "1" };
}

// Pointing at a spot height reads that scan. The map itself is drawn on the server.
export function TerrainReadout({ start, children, side }: { start: Reading; children: ReactNode; side: ReactNode }) {
  const [reading, setReading] = useState(start);
  const read = (event: PointerEvent | FocusEvent) => {
    const next = readSpot(event.target);
    if (next) setReading(next);
  };

  return (
    <div className="survey-map" onPointerOver={read} onFocus={read}>
      <div className="survey-plot">{children}</div>
      <div className="survey-side">
        <div className="reading" aria-live="polite">
          <p className="reading-name">{caseLabel(reading.id)}</p>
          <p className="reading-score">{reading.score}</p>
          <p className="reading-line">mean Dice</p>
          <dl>
            <div><dt>Tumor</dt><dd>{ml(Number(reading.tumor))} mL</dd></div>
            <div><dt>Kidney</dt><dd>{ml(Number(reading.kidney))} mL</dd></div>
          </dl>
          <p className="reading-open">{reading.open ? <a href={`/case/${reading.id}`}>Open this scan</a> : "Not in the gallery"}</p>
        </div>
        {side}
      </div>
    </div>
  );
}
