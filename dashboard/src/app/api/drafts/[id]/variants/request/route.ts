import { NextRequest, NextResponse } from "next/server";
import { getDraft, requestVariants } from "@/lib/db";

// Manager taps "Alternatives" — flag the draft so the polling agent generates them
export async function POST(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  if (!getDraft(id)) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({ draft: requestVariants(id) });
}
