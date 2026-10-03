import { NextResponse } from "next/server";

export async function POST() {
  return NextResponse.json({
    access_token: "v2_4_enterprise_session_token",
    refresh_token: "v2_4_enterprise_refresh_token",
    token_type: "bearer",
    user: {
      id: "admin-1",
      email: "admin@example.com",
      name: "Dr. Elena Vance",
      role: "admin",
    },
  });
}
