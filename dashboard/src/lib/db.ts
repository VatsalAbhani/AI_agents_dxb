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
}): Draft {
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
  };
  db()
    .prepare(
      `INSERT INTO drafts (id, client, channel, lead_name, lead_meta, draft, policy, status, created_at)
       VALUES (@id, @client, @channel, @lead_name, @lead_meta, @draft, @policy, @status, @created_at)`
    )
    .run(row);
  return row;
}

export function getDraft(id: string): Draft | undefined {
  return db().prepare("SELECT * FROM drafts WHERE id = ?").get(id) as Draft | undefined;
}

export function listDrafts(status: "pending" | "decided"): Draft[] {
  if (status === "pending") {
    return db()
      .prepare("SELECT * FROM drafts WHERE status = 'pending' ORDER BY created_at ASC")
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
  by: string
): Draft | undefined {
  const existing = getDraft(id);
  if (!existing || existing.status !== "pending") return existing;
  db()
    .prepare(
      `UPDATE drafts SET status = ?, final_text = ?, decided_by = ?, decided_at = ? WHERE id = ?`
    )
    .run(
      decision === "approve" ? "approved" : "rejected",
      decision === "approve" ? finalText ?? existing.draft : null,
      by,
      Date.now(),
      id
    );
  return getDraft(id);
}
