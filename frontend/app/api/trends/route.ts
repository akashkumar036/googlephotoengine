import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    trends: [
      {
        problem_id: "prob-1",
        label: "Temporal Chapter Blur (Chrono-Ambiguity)",
        growth_rate: 0.35,
        data_points: [
          { date: "2026-09-01", count: 120 },
          { date: "2026-09-08", count: 145 },
          { date: "2026-09-15", count: 180 },
          { date: "2026-09-22", count: 210 },
          { date: "2026-09-29", count: 245 },
        ],
      },
      {
        problem_id: "prob-2",
        label: "Visual Attribute Mismatch (Color/Garment)",
        growth_rate: 0.28,
        data_points: [
          { date: "2026-09-01", count: 90 },
          { date: "2026-09-08", count: 110 },
          { date: "2026-09-15", count: 135 },
          { date: "2026-09-22", count: 160 },
          { date: "2026-09-29", count: 195 },
        ],
      },
    ],
  });
}
