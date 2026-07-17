import { NextRequest, NextResponse } from "next/server";
import { getDraft } from "@/lib/db";

// Agent polls the decision
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const row = getDraft(id);
  if (!row) return NextResponse.json({ error: "not found" }, { status: 404 });
  return NextResponse.json({
    id: row.id,
    status: row.status,
    final: row.final_text,
    by: row.decided_by,
    reason: row.reason,
    variant: row.selected_variant,
    variants_requested: !!row.variants_requested,
    has_variants: !!row.variants,
  });
}
