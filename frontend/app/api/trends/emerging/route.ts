import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    emerging_problems: [
      {
        id: "em-1",
        title: "Cross-Device Deduplication Failure After OS Cloud Sync",
        statement: "Detected across Reddit and Google Play Store reviews: iCloud and Google Photos multi-sync causes duplicate walls on vacation queries.",
        growth_rate: 0.44,
        source_count: 2,
        first_observed: "2026-09-24",
      },
      {
        id: "em-2",
        title: "Pet Recognition Degradation Across Multi-Pet Households",
        statement: "App Store surge: Identically colored animals confused under night mode conditions, causing canine/feline cross-tagging.",
        growth_rate: 0.31,
        source_count: 2,
        first_observed: "2026-09-18",
      },
    ],
  });
}
