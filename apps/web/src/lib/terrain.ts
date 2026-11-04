import { contours } from "d3-contour";

// SPEC 013: the score terrain. Spot heights are real; the surface between them is smoothed.

export type Scan = { case_id: string; mean_dice: number; tumor_ml: number; kidney_ml: number };
export type Ring = [number, number][];
export type Tick = { value: number; at: number };

export const LEVELS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];

const TUMOR_ML = [0.04, 16000];
const KIDNEY_ML = [44, 1250];
const TUMOR_TICKS = [1, 10, 100, 1000];
const KIDNEY_TICKS = [100, 200, 400, 800];
const CELL = 7; // pixels per grid cell
const BANDWIDTH = 0.062; // kernel width, as a share of each axis
const REACH = 0.1; // the limit of survey sits this far from the nearest scans
const LIMIT = 0.72; // below 1, so a lone scan always stays inside the limit

const position = (value: number, [low, high]: number[]) =>
  (Math.log10(value) - Math.log10(low)) / (Math.log10(high) - Math.log10(low));

const toPath = (rings: Ring[][], cellX: number, cellY: number) =>
  rings
    .flat()
    .map((ring) => `M${ring.map(([x, y]) => `${(x * cellX).toFixed(1)} ${(y * cellY).toFixed(1)}`).join("L")}Z`)
    .join("");

export function terrain(scans: Scan[], width: number, height: number) {
  const nx = Math.ceil(width / CELL);
  const ny = Math.ceil(height / CELL);
  const points = scans.map((scan) => ({
    u: position(scan.tumor_ml, TUMOR_ML),
    v: position(scan.kidney_ml, KIDNEY_ML),
    height: scan.mean_dice,
  }));

  const surface = new Float64Array(nx * ny);
  const density = new Float64Array(nx * ny);
  for (let j = 0; j < ny; j += 1) {
    for (let i = 0; i < nx; i += 1) {
      const u = (i + 0.5) / nx;
      const v = 1 - (j + 0.5) / ny;
      let weight = 0;
      let total = 0;
      let reach = 0;
      for (const point of points) {
        const distance = (u - point.u) ** 2 + (v - point.v) ** 2;
        const w = Math.exp(-distance / (2 * BANDWIDTH ** 2));
        weight += w;
        total += w * point.height;
        reach += Math.exp(-distance / (2 * REACH ** 2));
      }
      surface[j * nx + i] = total / weight;
      density[j * nx + i] = reach;
    }
  }

  const cellX = width / nx;
  const cellY = height / ny;
  const field = contours().size([nx, ny]);
  return {
    width,
    height,
    bands: field.thresholds(LEVELS)(Array.from(surface)).map((band) => ({
      level: band.value,
      path: toPath(band.coordinates as Ring[][], cellX, cellY),
    })),
    limit: toPath(field.thresholds([LIMIT])(Array.from(density))[0].coordinates as Ring[][], cellX, cellY),
    spots: scans.map((scan, index) => ({ ...scan, x: points[index].u * width, y: (1 - points[index].v) * height })),
    tumorTicks: TUMOR_TICKS.map((value): Tick => ({ value, at: position(value, TUMOR_ML) * width })),
    kidneyTicks: KIDNEY_TICKS.map((value): Tick => ({ value, at: (1 - position(value, KIDNEY_ML)) * height })),
  };
}
