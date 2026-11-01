import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { build } from "./generate-data.mjs";

const REPORTS = resolve(import.meta.dirname, "../../../reports");

describe("generated results", () => {
  it("fails when the reports are missing", () => {
    const empty = mkdtempSync(join(tmpdir(), "reports-"));
    expect(() => build(empty)).toThrow(/Missing report file/);
    rmSync(empty, { recursive: true });
  });

  it("reads the measured test results", () => {
    const data = build(REPORTS);
    expect(data.nCases).toBe(73);
    expect(data.meanDice.mean).toBeGreaterThan(data.meanDice.low);
    expect(data.meanDice.mean).toBeLessThan(data.meanDice.high);
    expect(data.regions.map((r) => r.id)).toContain("cyst");
  });

  it("reads the speed of the setting the live demo uses", () => {
    const demo = build(REPORTS).speed.find((s) => s.setting === "no_tta_step_0.75");
    expect(demo?.nCases).toBe(6);
    expect(demo?.seconds).toBeGreaterThan(0);
  });

  it("keeps the failed cases in the gallery", () => {
    const groups = build(REPORTS).gallery.map((c) => c.group);
    expect(groups.filter((g) => g === "worst").length).toBe(groups.filter((g) => g === "best").length);
  });
});
