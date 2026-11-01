import { describe, expect, it, vi } from "vitest";
import { handleFeedback, handleRun, handleStats, type Store } from "./handlers";
import { MAX_COMMENT_CHARS } from "./validate";

const RUN = { status: "success", durationSeconds: 42.5, voxelCount: 1000, kidneyMl: 150, tumorMl: 12, cystMl: 0 };
const RUN_ID = "3f2b8a10-7c4e-4d21-9b6a-1e2f3a4b5c6d";

function store(overrides: Partial<Store> = {}): Store {
  return {
    addRun: vi.fn(async () => RUN_ID),
    addFeedback: vi.fn(async () => {}),
    stats: vi.fn(async () => ({ total: 3, succeeded: 2, medianSeconds: 40 })),
    ...overrides,
  };
}

const broken = () => Promise.reject(new Error("database is down"));

describe("POST /api/runs", () => {
  it("stores a valid run with the server's version", async () => {
    const db = store();
    const reply = await handleRun(JSON.stringify(RUN), db, "abc123");
    expect(reply).toEqual({ status: 201, body: { id: RUN_ID } });
    expect(db.addRun).toHaveBeenCalledWith({ ...RUN, appVersion: "abc123" });
  });

  it.each([
    ["not json", "{"],
    ["an array", "[]"],
    ["an unknown status", JSON.stringify({ ...RUN, status: "done" })],
    ["a negative duration", JSON.stringify({ ...RUN, durationSeconds: -1 })],
    ["a duration as text", JSON.stringify({ ...RUN, durationSeconds: "42" })],
    ["a fractional voxel count", JSON.stringify({ ...RUN, voxelCount: 1.5 })],
    ["a huge volume", JSON.stringify({ ...RUN, tumorMl: 1e9 })],
    ["a file name", JSON.stringify({ ...RUN, fileName: "patient.nii.gz" })],
  ])("rejects %s", async (_, text) => {
    const db = store();
    expect((await handleRun(text, db, "v")).status).toBe(400);
    expect(db.addRun).not.toHaveBeenCalled();
  });

  it("rejects an oversized body", async () => {
    expect((await handleRun("x".repeat(3000), store(), "v")).status).toBe(413);
  });

  it("answers 503 when the database fails or is not set up", async () => {
    expect((await handleRun(JSON.stringify(RUN), store({ addRun: broken }), "v")).status).toBe(503);
    expect((await handleRun(JSON.stringify(RUN), null, "v")).status).toBe(503);
  });
});

describe("POST /api/feedback", () => {
  it("stores a rating with or without a run", async () => {
    const db = store();
    const full = { runId: RUN_ID, rating: 5, comment: "Clear and fast" };
    expect((await handleFeedback(JSON.stringify(full), db)).status).toBe(201);
    expect(db.addFeedback).toHaveBeenCalledWith(full);
    await handleFeedback(JSON.stringify({ rating: 1 }), db);
    expect(db.addFeedback).toHaveBeenLastCalledWith({ runId: null, rating: 1, comment: null });
  });

  it.each([
    ["a rating of zero", { rating: 0 }],
    ["a rating of six", { rating: 6 }],
    ["a fractional rating", { rating: 2.5 }],
    ["a bad run id", { rating: 3, runId: "1; drop table feedback" }],
    ["a long comment", { rating: 3, comment: "x".repeat(MAX_COMMENT_CHARS + 1) }],
    ["an unknown field", { rating: 3, email: "a@b.c" }],
  ])("rejects %s", async (_, body) => {
    expect((await handleFeedback(JSON.stringify(body), store())).status).toBe(400);
  });

  it("answers 503 when the database fails", async () => {
    const reply = await handleFeedback(JSON.stringify({ rating: 4 }), store({ addFeedback: broken }));
    expect(reply.status).toBe(503);
  });
});

describe("GET /api/stats", () => {
  it("returns the counts", async () => {
    expect(await handleStats(store())).toEqual({ status: 200, body: { total: 3, succeeded: 2, medianSeconds: 40 } });
  });

  it("answers 503 when the database fails or is not set up", async () => {
    expect((await handleStats(store({ stats: broken }))).status).toBe(503);
    expect((await handleStats(null)).status).toBe(503);
  });
});
