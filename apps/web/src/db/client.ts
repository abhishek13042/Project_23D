import { neon } from "@neondatabase/serverless";
import { count, sql } from "drizzle-orm";
import { drizzle } from "drizzle-orm/neon-http";
import type { Store } from "@/lib/handlers";
import { feedback, inferenceRun } from "./schema";

// Returns null without a DATABASE_URL, so the site still works with no database (S011-REQ-001).
export function getStore(): Store | null {
  const url = process.env.DATABASE_URL;
  if (!url) return null;
  const db = drizzle(neon(url));
  return {
    async addRun(run) {
      const [row] = await db.insert(inferenceRun).values(run).returning({ id: inferenceRun.id });
      return row.id;
    },
    async addFeedback(item) {
      await db.insert(feedback).values(item);
    },
    async stats() {
      const [runs] = await db
        .select({
          total: count(),
          succeeded: sql<number>`count(*) filter (where ${inferenceRun.status} = 'success')`.mapWith(Number),
          medianSeconds: sql<number | null>`percentile_cont(0.5) within group (order by ${inferenceRun.durationSeconds})
            filter (where ${inferenceRun.status} = 'success')`.mapWith((v) => (v === null ? null : Number(v))),
        })
        .from(inferenceRun);
      return runs;
    },
  };
}
