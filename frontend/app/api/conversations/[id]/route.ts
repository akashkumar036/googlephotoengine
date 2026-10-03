import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const data = getDataset();
  const conv = data.conversations.find((c) => c.id === id) || data.conversations[0];

  if (!conv) {
    return NextResponse.json({ error: "Conversation not found" }, { status: 404 });
  }

  return NextResponse.json({
    ...conv,
    ai_analysis: {
      primary_intent: conv.primary_intent || "Find Personal Photo",
      memory_types: conv.memory_types || ["temporal", "visual"],
      failure_modes: conv.failure_modes || ["chrono_ambiguity"],
      frustration_level: conv.frustration_level || 0.8,
      severity: conv.severity || 0.75,
      confidence: conv.confidence || 0.88,
      user_goal: conv.user_goal || "Retrieve specific photo memory",
      known_memory: conv.known_memory || "Visual cues, context, season",
      unknown_memory: conv.unknown_memory || "Exact timestamp and location name",
    },
  });
}
