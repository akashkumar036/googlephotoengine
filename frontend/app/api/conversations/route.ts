import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(req: NextRequest) {
  const data = getDataset();
  const { searchParams } = new URL(req.url);
  const limit = parseInt(searchParams.get("limit") || "50", 10);
  const skip = parseInt(searchParams.get("skip") || "0", 10);
  const source = searchParams.get("source");
  const query = searchParams.get("query")?.toLowerCase();

  let filtered = data.conversations;

  if (source && source !== "all") {
    filtered = filtered.filter((c) => c.source === source);
  }

  if (query) {
    filtered = filtered.filter(
      (c) =>
        (c.text || "").toLowerCase().includes(query) ||
        (c.title || "").toLowerCase().includes(query) ||
        (c.user_goal || "").toLowerCase().includes(query)
    );
  }

  const results = filtered.slice(skip, skip + limit);

  return NextResponse.json({
    total: filtered.length,
    data: results,
  });
}
