import { NextResponse } from "next/server";
import { metrics } from "@/lib/db";

// Live pilot metrics — the numbers the weekly pilot report is built from.
export async function GET() {
  return NextResponse.json(metrics());
}
