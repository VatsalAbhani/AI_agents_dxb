import { NextRequest, NextResponse } from "next/server";
import { getDraft, setVariants } from "@/lib/db";

// Agent posts the generated alternatives (requires the agent api key)
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const key = process.env.GUARD_API_KEY ?? "demo-key";
  if ((req.headers.get("x-api-key") ?? "") !== key) {
    return NextResponse.json({ error: "invalid api key" }, { status: 401 });
  }
  const { id } = await params;
  if (!getDraft(id)) return NextResponse.json({ error: "not found" }, { status: 404 });
  const body = await req.json().catch(() => null);
  const variants = Array.isArray(body?.variants)
    ? body.variants.filter((v: unknown) => typeof v === "string" && v.trim()).slice(0, 3)
    : [];
  if (!variants.length) {
    return NextResponse.json({ error: "variants (string[]) required" }, { status: 400 });
  }
  return NextResponse.json({ draft: setVariants(id, variants) });
}
