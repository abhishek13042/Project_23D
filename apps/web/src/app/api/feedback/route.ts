import { getStore } from "@/db/client";
import { handleFeedback } from "@/lib/handlers";

export async function POST(request: Request) {
  const reply = await handleFeedback(await request.text(), getStore());
  return Response.json(reply.body, { status: reply.status });
}
