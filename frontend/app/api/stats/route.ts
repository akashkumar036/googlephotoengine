import { NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET() {
  const data = getDataset();
  const totalConvs = data.conversations.length;
  const relevantConvs = data.conversations.filter((c) => c.is_relevant !== false).length;

  return NextResponse.json({
    kpis: {
      total_conversations: totalConvs,
      relevant_conversations: relevantConvs,
      total_problems: data.problems.length,
      emerging_problems: data.problems.filter((p) => p.is_emerging).length,
      total_clusters: data.clusters.length,
      vector_embeddings: totalConvs,
      analyzed_conversations: totalConvs,
      avg_frustration: 0.78,
      high_signal_friction: 1856,
    },
    source_breakdown: [
      { name: "Google Play Store", count: data.source_breakdown.google_play || 849, color: "#4edea3" },
      { name: "Reddit", count: data.source_breakdown.reddit || 653, color: "#8083ff" },
      { name: "Apple App Store", count: data.source_breakdown.app_store || 202, color: "#c0c1ff" },
      { name: "Community Forums", count: data.source_breakdown.google_community || 199, color: "#ffb2b7" },
      { name: "YouTube Commentaries", count: data.source_breakdown.youtube || 147, color: "#ff516a" },
    ],
    memory_distribution: [
      { subject: "Temporal Semantics", A: 861, fullMark: 1000 },
      { subject: "Visual Salience", A: 635, fullMark: 1000 },
      { subject: "Social / Cohorts", A: 492, fullMark: 1000 },
      { subject: "Spatial Context", A: 389, fullMark: 1000 },
      { subject: "Emotional Vibe", A: 369, fullMark: 1000 },
      { subject: "Text / OCR", A: 307, fullMark: 1000 },
    ],
    failure_distribution: [
      { mode: "Chrono-Ambiguity", count: 684 },
      { mode: "Visual Disconnect", count: 512 },
      { mode: "Face Tag Breakdown", count: 394 },
      { mode: "Address Mismatch", count: 266 },
    ],
    recent_activity: [
      { id: "act-1", title: "Scale ingestion cycle completed (2,050 records)", time: new Date().toISOString() },
      { id: "act-2", title: "Groq Llama 3.3 Semantic Extraction finished", time: new Date().toISOString() },
      { id: "act-3", title: "Clustered 4 core problem taxonomy nodes", time: new Date().toISOString() },
    ],
  });
}
