import { NextRequest, NextResponse } from "next/server";
import { getDataset } from "@/lib/serverData";

export async function GET(req: NextRequest) {
  const data = getDataset();
  const { searchParams } = new URL(req.url);
  const limit = parseInt(searchParams.get("limit") || "100", 10);
  const skip = parseInt(searchParams.get("skip") || "0", 10);

  const results = data.problems.slice(skip, skip + limit);

  return NextResponse.json({
    total: data.problems.length,
    data: results,
  });
}
