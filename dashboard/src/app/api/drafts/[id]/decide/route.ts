import { NextRequest, NextResponse } from "next/server";
import { decideDraft, getDraft } from "@/lib/db";

// Manager decides from the dashboard: approve (optionally edited) or reject
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const existing = getDraft(id);
  if (!existing) return NextResponse.json({ error: "not found" }, { status: 404 });
  if (existing.status !== "pending") {
    return NextResponse.json({ error: "already decided" }, { status: 409 });
  }
  const body = await req.json().catch(() => null);
  const decision = body?.decision;
  if (decision !== "approve" && decision !== "reject") {
    return NextResponse.json(
      { error: "decision must be 'approve' or 'reject'" },
      { status: 400 }
    );
  }
  const finalText =
    typeof body.final === "string" && body.final.trim() ? body.final.trim() : null;
  const by = typeof body.by === "string" && body.by.trim() ? body.by.trim() : "Manager";
  const reason =
    typeof body.reason === "string" && body.reason.trim() ? body.reason.trim() : null;
  const row = decideDraft(id, decision, finalText, by, reason);
  return NextResponse.json({ draft: row });
}
