import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    benchmarks: [
      { id: "BM-01", name: "Chrono-Ambiguity Disambiguation", target_recall: 0.9, achieved_recall: 0.94 },
      { id: "BM-02", name: "Garment / Visual Saliency Extraction", target_recall: 0.85, achieved_recall: 0.89 },
      { id: "BM-03", name: "Cross-Platform Deduplication Accuracy", target_recall: 0.95, achieved_recall: 0.96 },
    ],
  });
}
