// SPEC 011: turn the report files into the data the website shows (S011-REQ-006).
// A missing report stops the build, so the site can never show empty or typed-in metrics.

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const REGIONS = [
  ["kidney_and_mass", "Kidney + masses"],
  ["mass", "Masses (tumor + cyst)"],
  ["tumor", "Tumor"],
  ["kidney", "Kidney"],
  ["cyst", "Cyst"],
];

function read(reports, path) {
  const file = join(reports, path);
  if (!existsSync(file)) throw new Error(`Missing report file: ${file}`);
  return JSON.parse(readFileSync(file, "utf-8"));
}

function readScans(reports, path) {
  const file = join(reports, path);
  if (!existsSync(file)) throw new Error(`Missing report file: ${file}`);
  const [header, ...lines] = readFileSync(file, "utf-8").trim().split(/\r?\n/);
  const columns = header.split(",");
  return lines.map((line) => {
    const cells = line.split(",");
    const value = (name) => cells[columns.indexOf(name)];
    return {
      case_id: value("case_id"),
      mean_dice: Number(value("mean_dice")),
      tumor_ml: Number(value("tumor_ref_ml")),
      kidney_ml: Number(value("kidney_ref_ml")),
    };
  });
}

const stat = (s) => ({ mean: s.mean, median: s.median, low: s.ci95[0], high: s.ci95[1] });
const rows = (table) =>
  table.map((r) => ({ group: r.group, n: r.n, mean: r.mean, median: r.median, low: r.ci95[0], high: r.ci95[1] }));

export function build(reports) {
  const test = read(reports, "evaluation/spec004/eval_pp/summary.json");
  const raw = read(reports, "evaluation/spec004/eval_raw/summary.json");
  const validation = read(reports, "evaluation/spec004/eval_val_pp/summary.json");
  const analysis = read(reports, "evaluation/spec004/analysis/analysis.json");
  const gallery = read(reports, "release/gallery_index.json");
  const benchmark = read(reports, "release/inference_benchmark.json");
  if (gallery.length === 0) throw new Error("The gallery index is empty");

  return {
    nCases: test.n_cases,
    meanDice: stat(test.primary.mean_dice),
    surfaceDice: stat(test.primary.mean_surface_dice),
    raw: { meanDice: stat(raw.primary.mean_dice), surfaceDice: stat(raw.primary.mean_surface_dice) },
    validation: {
      nCases: validation.n_cases,
      meanDice: stat(validation.primary.mean_dice),
      surfaceDice: stat(validation.primary.mean_surface_dice),
    },
    regions: REGIONS.map(([id, label]) => {
      const region = test.regions[id];
      return {
        id,
        label,
        official: Boolean(region.dice_official),
        dice: stat(region.dice_official ?? region.dice),
        surfaceDice: region.surface_dice_official ? stat(region.surface_dice_official) : null,
        nReference: (region.dice_official ?? region.dice).n,
      };
    }),
    bySize: rows(analysis.tables.size_bin.tumor_dice),
    byCyst: rows(analysis.tables.has_cyst.mean_dice),
    volumeCorrelation: analysis.tumor_volume_vs_tumor_dice,
    worstCases: analysis.worst_cases,
    scans: readScans(reports, "evaluation/spec004/eval_pp/per_case.csv"),
    speed: benchmark.settings.map((s) => ({
      setting: s.setting,
      seconds: s.seconds_per_case_mean,
      meanDice: s.mean_dice,
      nCases: s.n_cases,
    })),
    gallery,
  };
}

function main() {
  const reports = resolve(process.env.REPORTS_DIR ?? join(HERE, "../../../reports"));
  const out = join(HERE, "../src/data/results.json");
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, `${JSON.stringify(build(reports), null, 2)}\n`);
  console.log(`wrote ${out}`);
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
