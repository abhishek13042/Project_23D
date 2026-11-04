import { caseLabel, findCase, results, score } from "@/lib/results";
import { LEVELS, terrain } from "@/lib/terrain";

const BEST = "best";
const WORST = "worst";

function Mark({ group, size }: { group: string | null; size: number }) {
  if (group === BEST) return <path className="m-best" d={`M0 ${-size * 1.25}L${size * 1.15} ${size * 0.8}H${-size * 1.15}Z`} />;
  if (group === WORST) {
    const arm = size * 0.62;
    return (
      <>
        <circle className="m-worst" r={size * 1.05} />
        <path className="m-cross" d={`M${-arm} ${-arm}L${arm} ${arm}M${arm} ${-arm}L${-arm} ${arm}`} />
      </>
    );
  }
  return <circle className={group ? "m-gallery" : "m-scan"} r={group ? size * 0.8 : size * 0.42} />;
}

// One sheet of the survey. `labelled` names spots on the map, `leftLabels` sets those names to the
// left of their spot; `here` marks one scan on a locator.
export function ScoreTerrain({
  id,
  width,
  height,
  labelled = [],
  leftLabels = [],
  here,
  ticks = true,
  survey = false,
  dot = 7,
  className = "",
}: {
  id: string;
  width: number;
  height: number;
  labelled?: string[];
  leftLabels?: string[];
  here?: string;
  ticks?: boolean;
  survey?: boolean;
  dot?: number;
  className?: string;
}) {
  const sheet = terrain(results.scans, width, height);
  const clip = `limit-${id}`;

  return (
    <svg
      className={`terrain ${survey ? "surveying" : ""} ${className}`}
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Contour map of mean Dice for ${sheet.spots.length} test scans, by tumor volume and kidney volume. The table of scans gives the same scores.`}
    >
      <clipPath id={clip}>
        <path d={sheet.limit} />
      </clipPath>
      <rect className="ground" width={width} height={height} />
      {ticks && (
        <g className="graticule">
          {sheet.tumorTicks.map((tick) => <path key={tick.value} d={`M${tick.at} 0V${height}`} />)}
          {sheet.kidneyTicks.map((tick) => <path key={tick.value} d={`M0 ${tick.at}H${width}`} />)}
        </g>
      )}
      <g clipPath={`url(#${clip})`}>
        <rect className="band-0" width={width} height={height} />
        {sheet.bands.map((band) => (
          <path key={band.level} className={`band-${Math.round(band.level * 10)}`} fillRule="evenodd" d={band.path} />
        ))}
        {sheet.bands.map((band, index) => (
          <path
            key={band.level}
            className={Math.round(band.level * 10) === 5 ? "contour index" : "contour"}
            pathLength={1}
            style={survey ? { animationDelay: `${index * 110}ms` } : undefined}
            fillRule="evenodd"
            d={band.path}
          />
        ))}
      </g>
      <path className="limit" d={sheet.limit} />
      {ticks && (
        <g className="ticks">
          {sheet.tumorTicks.map((tick) => (
            <text key={tick.value} x={tick.at + 6} y={height - 10}>{tick.value} mL</text>
          ))}
          {sheet.kidneyTicks.map((tick) => (
            <text key={tick.value} x={10} y={tick.at - 6}>{tick.value} mL</text>
          ))}
        </g>
      )}
      <g className="spots">
        {sheet.spots
          .slice()
          .sort((a, b) => Number(Boolean(findCase(a.case_id))) - Number(Boolean(findCase(b.case_id))))
          .map((spot) => {
            const item = findCase(spot.case_id);
            const group = item ? (item.group === BEST || item.group === WORST ? item.group : "gallery") : null;
            const label = `${caseLabel(spot.case_id)}, mean Dice ${score(spot.mean_dice)}`;
            const data = {
              "data-case": spot.case_id,
              "data-score": score(spot.mean_dice),
              "data-tumor": spot.tumor_ml,
              "data-kidney": spot.kidney_ml,
              "data-open": item ? "1" : undefined,
            };
            const named = labelled.includes(spot.case_id);
            const right = spot.x > width * 0.72 || leftLabels.includes(spot.case_id);
            const body = (
              <>
                <circle className="reach" r={dot * 2.4} />
                <Mark group={here && here !== spot.case_id ? null : group} size={dot} />
                {named && (
                  <text className="spot-name" x={right ? -dot * 2 : dot * 2} y={dot * 0.6} textAnchor={right ? "end" : "start"}>
                    {caseLabel(spot.case_id)}: {score(spot.mean_dice)}
                  </text>
                )}
              </>
            );
            const place = `translate(${spot.x.toFixed(1)} ${spot.y.toFixed(1)})`;
            return item && !here ? (
              <g key={spot.case_id} transform={place}>
                <a href={`/case/${spot.case_id}`} aria-label={label} {...data}>
                  {body}
                </a>
              </g>
            ) : (
              <g
                key={spot.case_id}
                transform={place}
                className={here === spot.case_id ? "here" : here ? "faint" : undefined}
                {...(here ? {} : data)}
              >
                {body}
              </g>
            );
          })}
      </g>
    </svg>
  );
}

export function TerrainKey() {
  return (
    <div className="key">
      <div className="key-scale" aria-hidden="true">
        <span className="band-swatch band-0" />
        {LEVELS.map((level) => <span key={level} className={`band-swatch band-${Math.round(level * 10)}`} />)}
      </div>
      <div className="ruler-scale">
        <span>0</span>
        <span>0.5</span>
        <span>1</span>
      </div>
      <p className="key-title">Mean Dice, as height</p>
      <ul className="key-marks">
        <li><KeyMark group={WORST} /> Lowest scans</li>
        <li><KeyMark group={BEST} /> Best scans</li>
        <li><KeyMark group="gallery" /> Other gallery scans</li>
        <li><KeyMark group={null} /> All other scans</li>
      </ul>
    </div>
  );
}

function KeyMark({ group }: { group: string | null }) {
  return (
    <svg className="key-mark" viewBox="-11 -11 22 22" aria-hidden="true">
      <Mark group={group} size={6} />
    </svg>
  );
}
