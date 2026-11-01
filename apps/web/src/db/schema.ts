// SPEC 011: statistics only. No images, file names or IP addresses (S011-REQ-003).
// src/db/schema.sql creates these tables.

import { bigint, pgTable, real, smallint, text, timestamp, uuid } from "drizzle-orm/pg-core";

export const inferenceRun = pgTable("inference_run", {
  id: uuid("id").primaryKey().defaultRandom(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  status: text("status").notNull(),
  durationSeconds: real("duration_seconds").notNull(),
  voxelCount: bigint("voxel_count", { mode: "number" }),
  kidneyMl: real("kidney_ml"),
  tumorMl: real("tumor_ml"),
  cystMl: real("cyst_ml"),
  appVersion: text("app_version").notNull(),
});

export const feedback = pgTable("feedback", {
  id: uuid("id").primaryKey().defaultRandom(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  runId: uuid("run_id").references(() => inferenceRun.id, { onDelete: "set null" }),
  rating: smallint("rating").notNull(),
  comment: text("comment"),
});
