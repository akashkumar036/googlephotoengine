import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    starters: [
      "What kinds of old photos do users struggle to retrieve?",
      "What information do people actually remember about a photo?",
      "What information have users typically forgotten?",
      "How do users formulate searches when memory is incomplete?",
      "Which platform reports the highest rate of photo search abandonment?",
    ],
  });
}
