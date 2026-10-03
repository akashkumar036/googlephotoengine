import { NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET() {
  const data = getDataset();
  return NextResponse.json({
    status: "ok",
    version: "v2.4 Enterprise AI",
    total_conversations: data.metadata.total_conversations,
    uptime_ms: 18,
  });
}
