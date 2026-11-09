// SPEC 011: route logic with the database passed in, so it can be tested without one.

import { MAX_BODY_BYTES, parseFeedback, parseRun, type FeedbackInput, type RunInput } from "./validate";

export type Stats = { total: number; succeeded: number; medianSeconds: number | null };

export type Store = {
  addRun(run: RunInput & { appVersion: string }): Promise<string>;
  addFeedback(item: FeedbackInput): Promise<void>;
  stats(): Promise<Stats>;
};

type Reply = { status: number; body: Record<string, unknown> };

const INVALID: Reply = { status: 400, body: { error: "invalid input" } };
const TOO_LARGE: Reply = { status: 413, body: { error: "too large" } };
const UNAVAILABLE: Reply = { status: 503, body: { error: "statistics are unavailable" } };

function parseBody(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

async function guarded(store: Store | null, action: (store: Store) => Promise<Reply>): Promise<Reply> {
  if (!store) return UNAVAILABLE;
  try {
    return await action(store);
  } catch (error) {
    console.error("database request failed", error instanceof Error ? error.message : error);
    return UNAVAILABLE;
  }
}

export async function handleRun(text: string, store: Store | null, appVersion: string): Promise<Reply> {
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) return TOO_LARGE;
  const run = parseRun(parseBody(text));
  if (!run) return INVALID;
  return guarded(store, async (db) => ({ status: 201, body: { id: await db.addRun({ ...run, appVersion }) } }));
}

export async function handleFeedback(text: string, store: Store | null): Promise<Reply> {
  if (new TextEncoder().encode(text).length > MAX_BODY_BYTES) return TOO_LARGE;
  const item = parseFeedback(parseBody(text));
  if (!item) return INVALID;
  return guarded(store, async (db) => {
    await db.addFeedback(item);
    return { status: 201, body: { ok: true } };
  });
}

export function handleStats(store: Store | null): Promise<Reply> {
  return guarded(store, async (db) => ({ status: 200, body: await db.stats() }));
}
