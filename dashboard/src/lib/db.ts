import Database from "better-sqlite3";
import path from "path";
import fs from "fs";
import crypto from "crypto";

export type Draft = {
  id: string;
  client: string;
  channel: string;
  lead_name: string;
  lead_meta: string | null; // JSON: source, phone (redacted), enquiry…
  draft: string;
  policy: string | null; // JSON: array of reason strings
  status: "pending" | "approved" | "rejected";
  final_text: string | null;
  decided_by: string | null;
  created_at: number;
  decided_at: number | null;
  intent: string | null; // JSON: {tier, action, high_intent}
  relationship: string | null; // new | returning | referral | personal
  reason: string | null; // why the manager edited/rejected
  priority: number; // 1 = high-intent (sorted first)
  variants: string | null; // JSON: alternative phrasings, generated on demand
  variants_requested: number; // 1 = manager tapped "Alternatives", agent is generating
  selected_variant: number | null; // which alternative was sent (null = primary/edited)
};

// singleton so Next.js HMR doesn't open a new handle per reload
const g = globalThis as unknown as { __guardDb?: Database.Database };

export function db(): Database.Database {
  if (!g.__guardDb) {
    const dir = path.join(process.cwd(), "data");
    fs.mkdirSync(dir, { recursive: true });
    const handle = new Database(path.join(dir, "guard.db"));
    handle.pragma("journal_mode = WAL");
    handle.exec(`
      CREATE TABLE IF NOT EXISTS drafts (
        id TEXT PRIMARY KEY,
        client TEXT NOT NULL DEFAULT 'demo',
        channel TEXT NOT NULL DEFAULT 'whatsapp',
        lead_name TEXT NOT NULL DEFAULT 'Lead',
        lead_meta TEXT,
        draft TEXT NOT NULL,
        policy TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        final_text TEXT,
        decided_by TEXT,
        created_at INTEGER NOT NULL,
        decided_at INTEGER
      );
      CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status, created_at);
    `);
    // additive migrations for databases created before these columns existed
    const cols = (handle.prepare("PRAGMA table_info(drafts)").all() as { name: string }[])
      .map((c) => c.name);
    for (const [col, ddl] of [
      ["intent", "ALTER TABLE drafts ADD COLUMN intent TEXT"],
      ["relationship", "ALTER TABLE drafts ADD COLUMN relationship TEXT"],
      ["reason", "ALTER TABLE drafts ADD COLUMN reason TEXT"],
      ["priority", "ALTER TABLE drafts ADD COLUMN priority INTEGER NOT NULL DEFAULT 0"],
      ["variants", "ALTER TABLE drafts ADD COLUMN variants TEXT"],
      ["variants_requested", "ALTER TABLE drafts ADD COLUMN variants_requested INTEGER NOT NULL DEFAULT 0"],
      ["selected_variant", "ALTER TABLE drafts ADD COLUMN selected_variant INTEGER"],
    ] as const) {
      if (!cols.includes(col)) handle.exec(ddl);
    }
    g.__guardDb = handle;
  }
  return g.__guardDb;
}

export function insertDraft(input: {
  client?: string;
  channel?: string;
  lead_name?: string;
  lead_meta?: unknown;
  draft: string;
  policy?: unknown;
  intent?: unknown;
  relationship?: string;
  variants?: string[];
}): Draft {
  const intent = input.intent && typeof input.intent === "object" ? input.intent : null;
  const highIntent = !!(intent as { high_intent?: boolean } | null)?.high_intent;
  const row: Draft = {
    id: crypto.randomUUID(),
    client: input.client ?? "demo",
    channel: input.channel ?? "whatsapp",
    lead_name: input.lead_name ?? "Lead",
    lead_meta: input.lead_meta ? JSON.stringify(input.lead_meta) : null,
    draft: input.draft,
    policy: input.policy ? JSON.stringify(input.policy) : null,
    status: "pending",
    final_text: null,
    decided_by: null,
    created_at: Date.now(),
    decided_at: null,
    intent: intent ? JSON.stringify(intent) : null,
    relationship: input.relationship ?? null,
    reason: null,
    priority: highIntent ? 1 : 0,
    variants: input.variants?.length ? JSON.stringify(input.variants) : null,
    variants_requested: 0,
    selected_variant: null,
  };
  db()
    .prepare(
      `INSERT INTO drafts (id, client, channel, lead_name, lead_meta, draft, policy, status, created_at,
                           intent, relationship, priority, variants)
       VALUES (@id, @client, @channel, @lead_name, @lead_meta, @draft, @policy, @status, @created_at,
               @intent, @relationship, @priority, @variants)`
    )
    .run(row);
  return row;
}

export function requestVariants(id: string): Draft | undefined {
  const existing = getDraft(id);
  if (!existing || existing.status !== "pending") return existing;
  db().prepare("UPDATE drafts SET variants_requested = 1 WHERE id = ?").run(id);
  return getDraft(id);
}

export function setVariants(id: string, variants: string[]): Draft | undefined {
  const existing = getDraft(id);
  if (!existing || existing.status !== "pending") return existing;
  db()
    .prepare("UPDATE drafts SET variants = ? WHERE id = ?")
    .run(JSON.stringify(variants), id);
  return getDraft(id);
}

export function getDraft(id: string): Draft | undefined {
  return db().prepare("SELECT * FROM drafts WHERE id = ?").get(id) as Draft | undefined;
}

export function listDrafts(status: "pending" | "decided"): Draft[] {
  if (status === "pending") {
    // high-intent leads jump the queue — the handoff clock is running
    return db()
      .prepare("SELECT * FROM drafts WHERE status = 'pending' ORDER BY priority DESC, created_at ASC")
      .all() as Draft[];
  }
  return db()
    .prepare(
      "SELECT * FROM drafts WHERE status != 'pending' ORDER BY decided_at DESC LIMIT 50"
    )
    .all() as Draft[];
}

export function decideDraft(
  id: string,
  decision: "approve" | "reject",
  finalText: string | null,
  by: string,
  reason: string | null = null,
  variant: number | null = null
): Draft | undefined {
  const existing = getDraft(id);
  if (!existing || existing.status !== "pending") return existing;
  db()
    .prepare(
      `UPDATE drafts SET status = ?, final_text = ?, decided_by = ?, decided_at = ?, reason = ?,
                         selected_variant = ? WHERE id = ?`
    )
    .run(
      decision === "approve" ? "approved" : "rejected",
      decision === "approve" ? finalText ?? existing.draft : null,
      by,
      Date.now(),
      reason,
      variant,
      id
    );
  return getDraft(id);
}

function median(values: number[]): number | null {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : Math.round((s[mid - 1] + s[mid]) / 2);
}

// the pilot metrics sheet, computed live from the queue
export function metrics() {
  const rows = db().prepare("SELECT * FROM drafts").all() as Draft[];
  const decided = rows.filter((d) => d.status !== "pending" && d.decided_at);
  const approved = decided.filter((d) => d.status === "approved");
  const unchanged = approved.filter((d) => d.final_text === d.draft);
  const edited = approved.filter((d) => d.final_text !== d.draft);
  const rejected = decided.filter((d) => d.status === "rejected");
  const decisionTimes = decided.map((d) => (d.decided_at as number) - d.created_at);
  const handoffTimes = decided
    .filter((d) => d.priority === 1)
    .map((d) => (d.decided_at as number) - d.created_at);
  return {
    pending: rows.length - decided.length,
    decided: decided.length,
    approved_unchanged: unchanged.length,
    approved_edited: edited.length,
    rejected: rejected.length,
    pct_approved_unchanged: decided.length
      ? Math.round((unchanged.length / decided.length) * 100)
      : null,
    pct_edited: decided.length ? Math.round((edited.length / decided.length) * 100) : null,
    pct_rejected: decided.length ? Math.round((rejected.length / decided.length) * 100) : null,
    median_decision_ms: median(decisionTimes),
    median_handoff_ms: median(handoffTimes),
    high_intent_total: rows.filter((d) => d.priority === 1).length,
    high_intent_decided: handoffTimes.length,
  };
}
