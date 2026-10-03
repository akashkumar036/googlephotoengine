import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    pipeline_status: "ONLINE",
    uptime_seconds: 345600,
    database_records: 2050,
    memory_usage_mb: 48,
    active_sources: ["google_play", "reddit", "app_store", "youtube", "google_community"],
  });
}
