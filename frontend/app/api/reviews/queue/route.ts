import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(req: NextRequest) {
  const data = getDataset();
  const queue = data.conversations.slice(0, 12).map((c) => ({
    id: `rev-${c.id}`,
    conversation_id: c.id,
    source: c.source,
    text: c.text,
    suggested_intent: c.primary_intent || "Find Photo",
    suggested_memory_types: c.memory_types || ["temporal"],
    suggested_failure_modes: c.failure_modes || ["chrono_ambiguity"],
    ai_confidence: c.confidence || 0.85,
    status: "pending",
  }));

  return NextResponse.json({
    total: 12,
    queue,
  });
}
