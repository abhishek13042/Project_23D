import { getStore } from "@/db/client";
import { handleRun } from "@/lib/handlers";

export async function POST(request: Request) {
  const version = process.env.VERCEL_GIT_COMMIT_SHA?.slice(0, 12) ?? "local";
  const reply = await handleRun(await request.text(), getStore(), version);
  return Response.json(reply.body, { status: reply.status });
}
