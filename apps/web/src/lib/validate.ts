// SPEC 011: database input checks (S011-REQ-009). Only known fields pass, so a client can't slip a
// file name or anything else into the database (S011-REQ-003).

export const MAX_BODY_BYTES = 2048;
export const MAX_COMMENT_CHARS = 1000;
const MAX_DURATION_SECONDS = 3600;
const MAX_VOXELS = 2_000_000_000;
const MAX_VOLUME_ML = 100_000;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const RUN_FIELDS = ["status", "durationSeconds", "voxelCount", "kidneyMl", "tumorMl", "cystMl"];
const FEEDBACK_FIELDS = ["runId", "rating", "comment"];

export type RunInput = {
  status: "success" | "failed";
  durationSeconds: number;
  voxelCount: number | null;
  kidneyMl: number | null;
  tumorMl: number | null;
  cystMl: number | null;
};

export type FeedbackInput = { runId: string | null; rating: number; comment: string | null };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

const onlyFields = (body: Record<string, unknown>, fields: string[]) =>
  Object.keys(body).every((key) => fields.includes(key));

const inRange = (value: unknown, max: number): value is number =>
  typeof value === "number" && Number.isFinite(value) && value >= 0 && value <= max;

const optionalInRange = (value: unknown, max: number) => value === null || value === undefined || inRange(value, max);

export function parseRun(body: unknown): RunInput | null {
  if (!isRecord(body) || !onlyFields(body, RUN_FIELDS)) return null;
  const { status, durationSeconds, voxelCount, kidneyMl, tumorMl, cystMl } = body;
  if (status !== "success" && status !== "failed") return null;
  if (!inRange(durationSeconds, MAX_DURATION_SECONDS)) return null;
  if (!optionalInRange(voxelCount, MAX_VOXELS) || (typeof voxelCount === "number" && !Number.isInteger(voxelCount))) {
    return null;
  }
  if (![kidneyMl, tumorMl, cystMl].every((v) => optionalInRange(v, MAX_VOLUME_ML))) return null;
  return {
    status,
    durationSeconds,
    voxelCount: (voxelCount as number | null | undefined) ?? null,
    kidneyMl: (kidneyMl as number | null | undefined) ?? null,
    tumorMl: (tumorMl as number | null | undefined) ?? null,
    cystMl: (cystMl as number | null | undefined) ?? null,
  };
}

export function parseFeedback(body: unknown): FeedbackInput | null {
  if (!isRecord(body) || !onlyFields(body, FEEDBACK_FIELDS)) return null;
  const { runId, rating, comment } = body;
  if (typeof rating !== "number" || !Number.isInteger(rating) || rating < 1 || rating > 5) return null;
  if (runId !== null && runId !== undefined && !(typeof runId === "string" && UUID.test(runId))) return null;
  if (comment !== null && comment !== undefined) {
    if (typeof comment !== "string" || comment.length > MAX_COMMENT_CHARS) return null;
  }
  return { runId: (runId as string | null | undefined) ?? null, rating, comment: (comment as string) || null };
}
