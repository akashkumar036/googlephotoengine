import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(req: NextRequest) {
  const data = getDataset();
  const { searchParams } = new URL(req.url);
  const q = (searchParams.get("q") || "").toLowerCase().trim();
  const limit = parseInt(searchParams.get("limit") || "40", 10);

  let results: any[] = data.conversations;

  if (q) {
    const terms = q.split(" ").filter((w) => w.length > 1);
    results = results
      .map((c: any) => {
        const text = (c.text || "").toLowerCase();
        const title = (c.title || "").toLowerCase();
        const goal = (c.user_goal || "").toLowerCase();
        const summary = (c.reasoning_summary || "").toLowerCase();

        let score = 0;
        terms.forEach((term) => {
          if (title.includes(term)) score += 3;
          if (goal.includes(term)) score += 2;
          if (summary.includes(term)) score += 2;
          if (text.includes(term)) score += 1;
        });

        return { ...c, score };
      })
      .filter((c: any) => c.score > 0)
      .sort((a: any, b: any) => b.score - a.score);
  }

  const mapped = results.slice(0, limit).map((c) => ({
    ...c,
    source: c.source || "reddit",
    similarity_score: Math.min(0.98, 0.7 + (c.score || 1) * 0.05),
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
    total: mapped.length,
    data: mapped,
  });
}
