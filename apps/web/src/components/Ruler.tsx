const percent = (value: number) => `${Math.min(Math.max(value, 0), 1) * 100}%`;

// The site's one chart: a score on a 0–1 scale, with its 95% interval when there is one
export function Ruler({ value, low, high }: { value: number; low?: number; high?: number }) {
  const range = low === undefined || high === undefined ? "" : `, 95% interval ${low.toFixed(3)} to ${high.toFixed(3)}`;
  const label = `${value.toFixed(3)}${range}`;
  return (
    <div className="ruler" role="img" aria-label={label} title={label}>
      {low !== undefined && high !== undefined && (
        <span className="span" style={{ left: percent(low), width: `${(high - low) * 100}%` }} />
      )}
      <span className="mark" style={{ left: percent(value) }} />
    </div>
  );
}

export function RulerScale() {
  return (
    <div className="ruler-scale" aria-hidden="true">
      <span>0</span>
      <span>0.5</span>
      <span>1</span>
    </div>
  );
}
