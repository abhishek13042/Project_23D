import { getStore } from "@/db/client";
import { handleStats } from "@/lib/handlers";

// The CDN answers for five minutes, so most visits don't wake the free database
const CACHE = "public, s-maxage=300, stale-while-revalidate=600";

export async function GET() {
  const reply = await handleStats(getStore());
  const headers = reply.status === 200 ? { "Cache-Control": CACHE } : { "Cache-Control": "no-store" };
  return Response.json(reply.body, { status: reply.status, headers });
}
