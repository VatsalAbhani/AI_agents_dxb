import { NextRequest, NextResponse } from "next/server";
import { insertDraft, listDrafts } from "@/lib/db";

function agentAuthed(req: NextRequest): boolean {
  const key = process.env.GUARD_API_KEY ?? "demo-key";
  return (req.headers.get("x-api-key") ?? "") === key;
}

// Agent submits a draft for approval
export async function POST(req: NextRequest) {
  if (!agentAuthed(req)) {
    return NextResponse.json({ error: "invalid api key" }, { status: 401 });
  }
  const body = await req.json().catch(() => null);
  if (!body || typeof body.draft !== "string" || !body.draft.trim()) {
    return NextResponse.json({ error: "draft (string) is required" }, { status: 400 });
  }
  const row = insertDraft({
    client: typeof body.client === "string" ? body.client : undefined,
    channel: typeof body.channel === "string" ? body.channel : undefined,
    lead_name:
      typeof body.lead?.name === "string" ? body.lead.name : undefined,
    lead_meta: body.lead ?? undefined,
    draft: body.draft,
    policy: Array.isArray(body.policy) ? body.policy : undefined,
    intent: body.intent ?? undefined,
    relationship: typeof body.relationship === "string" ? body.relationship : undefined,
  });
  return NextResponse.json({ id: row.id, status: row.status }, { status: 201 });
}

// Dashboard lists drafts (?status=pending|decided)
export async function GET(req: NextRequest) {
  const status = req.nextUrl.searchParams.get("status") === "decided" ? "decided" : "pending";
  return NextResponse.json({ drafts: listDrafts(status) });
}
