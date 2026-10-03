import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(req: NextRequest) {
  const data = getDataset();
  const { searchParams } = new URL(req.url);
  const limit = parseInt(searchParams.get("limit") || "100", 10);
  const skip = parseInt(searchParams.get("skip") || "0", 10);
  const source = searchParams.get("source")?.toLowerCase();
  const query = (searchParams.get("query") || searchParams.get("q") || "").toLowerCase().trim();
  const isRelevantParam = searchParams.get("is_relevant");

  let filtered = data.conversations;

  // Filter by relevance if requested
  if (isRelevantParam === "true" || isRelevantParam === "1") {
    filtered = filtered.filter((c) => Boolean(c.is_relevant) || c.is_relevant === undefined);
  }

  // Filter by source
  if (source && source !== "all") {
    filtered = filtered.filter((c) => c.source?.toLowerCase() === source);
  }

  // Filter by query
  if (query) {
    const words = query.split(" ").filter((w) => w.length > 1);
    filtered = filtered.filter((c) => {
      const text = (c.text || "").toLowerCase();
      const title = (c.title || "").toLowerCase();
      const goal = (c.user_goal || "").toLowerCase();
      const summary = (c.reasoning_summary || "").toLowerCase();
      return words.some(
        (w) => text.includes(w) || title.includes(w) || goal.includes(w) || summary.includes(w)
      );
    });
  }

  const results = filtered.slice(skip, skip + limit).map((c) => ({
    ...c,
    source: c.source || "reddit",
    analysis: {
      primary_intent: c.primary_intent || "Find Personal Photo",
      memory_types: c.memory_types || ["temporal", "visual"],
      retrieval_strategies: c.retrieval_strategies || ["keyword_search"],
      failure_modes: c.failure_modes || ["chrono_ambiguity"],
      pain_points: c.pain_points || [],
      user_goal: c.user_goal || "Find specific photo",
      known_memory: c.known_memory || "Visual cues, context",
      unknown_memory: c.unknown_memory || "Exact timestamp",
      frustration_level: c.frustration_level ?? 0.78,
      severity: c.severity ?? 0.75,
      confidence: c.confidence ?? 0.88,
      reasoning_summary: c.reasoning_summary || c.user_goal,
    },
  }));

  return NextResponse.json({
    total: filtered.length,
    data: results,
  });
}
