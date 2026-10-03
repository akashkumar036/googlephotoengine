import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const data = getDataset();
  const problem = data.problems.find((p) => p.id === id) || data.problems[0];

  if (!problem) {
    return NextResponse.json({ error: "Problem not found" }, { status: 404 });
  }

  // Sample matching conversations for evidence tab
  const evidenceSamples = data.conversations
    .filter((c) => (c.failure_modes || []).length > 0)
    .slice(0, 8)
    .map((c) => ({
      id: c.id,
      conversation_id: c.id,
      source: c.source,
      date: c.created_at,
      excerpt: c.text?.slice(0, 240) + "...",
      primary_intent: c.primary_intent,
      memory_types: c.memory_types,
      confidence: c.confidence || 0.85,
    }));

  return NextResponse.json({
    ...problem,
    evidence: evidenceSamples,
    trends: [
      { date: "2026-09-01", count: 18 },
      { date: "2026-09-08", count: 24 },
      { date: "2026-09-15", count: 35 },
      { date: "2026-09-22", count: 48 },
      { date: "2026-09-29", count: 62 },
    ],
  });
}
