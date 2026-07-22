"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

type Draft = {
  id: string;
  client: string;
  channel: string;
  lead_name: string;
  lead_meta: string | null;
  draft: string;
  policy: string | null;
  status: "pending" | "approved" | "rejected";
  final_text: string | null;
  decided_by: string | null;
  created_at: number;
  decided_at: number | null;
  intent: string | null;
  relationship: string | null;
  reason: string | null;
  priority: number;
  variants: string | null;
  variants_requested: number;
  variants_requested_at: number | null;
  selected_variant: number | null;
};

function parseVariants(d: Draft): string[] {
  try {
    const v = d.variants ? JSON.parse(d.variants) : null;
    return Array.isArray(v) ? v.map(String) : [];
  } catch {
    return [];
  }
}

type Metrics = {
  pending: number;
  decided: number;
  pct_approved_unchanged: number | null;
  pct_edited: number | null;
  pct_rejected: number | null;
  median_decision_ms: number | null;
  median_handoff_ms: number | null;
  high_intent_total: number;
  high_intent_decided: number;
};

function fmtMs(ms: number | null): string {
  if (ms === null) return "—";
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
}

function timeAgo(ts: number): string {
  const s = Math.max(1, Math.floor((Date.now() - ts) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function meta(d: Draft): { source?: string; enquiry?: string } {
  try {
    return d.lead_meta ? JSON.parse(d.lead_meta) : {};
  } catch {
    return {};
  }
}

function policyChips(d: Draft): string[] {
  try {
    const p = d.policy ? JSON.parse(d.policy) : null;
    if (Array.isArray(p) && p.length) return p.map(String);
  } catch {
    /* fall through */
  }
  return ["HUMAN APPROVAL REQUIRED"];
}

export function ApprovalsFeed() {
  const [pending, setPending] = useState<Draft[]>([]);
  const [decided, setDecided] = useState<Draft[]>([]);
  const [editing, setEditing] = useState<Draft | null>(null);
  const [editText, setEditText] = useState("");
  const [editReason, setEditReason] = useState("");
  const [rejecting, setRejecting] = useState<Draft | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [stats, setStats] = useState<Metrics | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [p, d, m] = await Promise.all([
        fetch("/api/drafts?status=pending").then((r) => r.json()),
        fetch("/api/drafts?status=decided").then((r) => r.json()),
        fetch("/api/metrics").then((r) => r.json()),
      ]);
      setPending(p.drafts ?? []);
      setDecided(d.drafts ?? []);
      setStats(m ?? null);
      setLoaded(true);
    } catch {
      /* transient — next poll will retry */
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [refresh]);

  async function requestAlternatives(d: Draft) {
    await fetch(`/api/drafts/${d.id}/variants/request`, { method: "POST" });
    toast.message("Asking the agent for alternative phrasings…");
    refresh();
  }

  async function decide(
    d: Draft,
    decision: "approve" | "reject",
    finalText?: string,
    reason?: string,
    variant?: number
  ) {
    setBusy(d.id);
    try {
      const res = await fetch(`/api/drafts/${d.id}/decide`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision, final: finalText, by: "Manager", reason, variant }),
      });
      if (!res.ok) throw new Error(await res.text());
      toast.success(
        decision === "approve"
          ? finalText
            ? "Approved with edits — sending"
            : "Approved — sending"
          : "Rejected — nothing sent"
      );
      setEditing(null);
      setRejecting(null);
      setEditReason("");
      setRejectReason("");
      await refresh();
    } catch {
      toast.error("Could not save the decision — try again");
    } finally {
      setBusy(null);
    }
  }

  async function seedDemo() {
    await fetch("/api/demo", { method: "POST" });
    toast.success("Demo drafts loaded");
    refresh();
  }

  return (
    <div className="w-full">
      {stats && stats.decided + stats.pending > 0 && (
        <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            { label: "PENDING", value: String(stats.pending) },
            { label: "MEDIAN DECISION", value: fmtMs(stats.median_decision_ms) },
            {
              label: "APPROVED UNCHANGED",
              value: stats.pct_approved_unchanged === null ? "—" : `${stats.pct_approved_unchanged}%`,
            },
            {
              label: "HIGH-INTENT HANDOFF",
              value: `${fmtMs(stats.median_handoff_ms)} · ${stats.high_intent_decided}/${stats.high_intent_total}`,
            },
          ].map((s) => (
            <div key={s.label} className="rounded-md border bg-card px-3 py-2">
              <p className="font-mono text-[9px] tracking-[0.15em] text-muted-foreground">{s.label}</p>
              <p className="mt-0.5 text-sm font-semibold tabular-nums">{s.value}</p>
            </div>
          ))}
        </div>
      )}
    <Tabs defaultValue="pending" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="pending">
          Pending
          {pending.length > 0 && (
            <Badge className="ml-2 bg-primary text-primary-foreground">{pending.length}</Badge>
          )}
        </TabsTrigger>
        <TabsTrigger value="activity">Activity</TabsTrigger>
      </TabsList>

      <TabsContent value="pending" className="mt-4 space-y-4">
        {loaded && pending.length === 0 && (
          <Card>
            <CardContent className="flex flex-col items-center gap-4 py-12 text-center">
              <p className="font-mono text-xs tracking-widest text-muted-foreground">
                NO DRAFTS WAITING — THE AGENT IS HANDLING IT
              </p>
              <Button variant="outline" size="sm" onClick={seedDemo}>
                Load demo data
              </Button>
            </CardContent>
          </Card>
        )}

        {pending.map((d) => {
          const m = meta(d);
          const relationshipLead = d.relationship && d.relationship !== "new";
          const variants = parseVariants(d);
          return (
            <Card
              key={d.id}
              className={
                d.priority === 1
                  ? "overflow-hidden border-primary ring-1 ring-primary/40"
                  : "overflow-hidden"
              }
            >
              <CardHeader className="pb-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-base font-semibold">{d.lead_name}</span>
                  {d.priority === 1 && (
                    <Badge className="bg-primary font-mono text-[10px] text-primary-foreground whitespace-normal">
                      ⚡ HIGH INTENT · CLOCK RUNNING
                    </Badge>
                  )}
                  {relationshipLead && (
                    <Badge
                      variant="secondary"
                      className="font-mono text-[10px] uppercase whitespace-normal"
                      title="Relationship lead — the approved text goes to the assigned advisor to send personally"
                    >
                      ✋ {d.relationship} · HUMAN SENDER
                    </Badge>
                  )}
                  <Badge variant="secondary" className="font-mono text-[10px] uppercase">
                    {d.channel}
                  </Badge>
                  {m.source && m.source.toLowerCase() !== d.channel.toLowerCase() && (
                    <Badge variant="outline" className="font-mono text-[10px] uppercase">
                      {m.source}
                    </Badge>
                  )}
                  <span className="ml-auto font-mono text-xs text-muted-foreground">
                    {timeAgo(d.created_at)}
                  </span>
                </div>
                {relationshipLead && (
                  <p className="text-xs text-muted-foreground">
                    Draft-only lead: approving hands the text to the assigned advisor — the
                    bot will not send it.
                  </p>
                )}
                {m.enquiry && (
                  <p className="text-sm text-muted-foreground">Enquiry: {m.enquiry}</p>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="rounded-md border bg-muted/40 p-3 text-base leading-relaxed">
                  {d.draft}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {policyChips(d).map((c) => (
                    <Badge
                      key={c}
                      variant="outline"
                      className="border-primary/50 font-mono text-[10px] text-primary"
                    >
                      {c}
                    </Badge>
                  ))}
                </div>
                {variants.length > 0 && (
                  <div className="space-y-2">
                    <p className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground">
                      ALTERNATIVES — TAP TO SEND INSTEAD
                    </p>
                    {variants.map((v, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-2 rounded-md border border-dashed p-2.5"
                      >
                        <p className="flex-1 text-sm leading-relaxed">{v}</p>
                        <Button
                          size="sm"
                          variant="outline"
                          className="shrink-0"
                          disabled={busy === d.id}
                          onClick={() => decide(d, "approve", v, undefined, i)}
                        >
                          Send this
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                {variants.length === 0 && !!d.variants_requested &&
                  (!d.variants_requested_at || Date.now() - d.variants_requested_at > 25000 ? (
                    <p className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground">
                      NO LIVE AGENT ON THIS DRAFT — APPROVE OR EDIT INSTEAD
                    </p>
                  ) : (
                    <p className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground">
                      GENERATING ALTERNATIVES — THE AGENT IS WRITING…
                    </p>
                  ))}
              </CardContent>
              <CardFooter className="gap-2">
                <Button
                  className="h-12 flex-1 text-base"
                  disabled={busy === d.id}
                  onClick={() => decide(d, "approve")}
                >
                  Approve
                </Button>
                <Button
                  variant="secondary"
                  className="h-12"
                  disabled={busy === d.id}
                  onClick={() => {
                    setEditing(d);
                    setEditText(d.draft);
                    setEditReason("");
                  }}
                >
                  Edit
                </Button>
                {variants.length === 0 && !d.variants_requested && (
                  <Button
                    variant="secondary"
                    className="h-12"
                    disabled={busy === d.id}
                    onClick={() => requestAlternatives(d)}
                  >
                    Alternatives
                  </Button>
                )}
                <Button
                  variant="outline"
                  className="h-12 text-destructive hover:text-destructive"
                  disabled={busy === d.id}
                  onClick={() => {
                    setRejecting(d);
                    setRejectReason("");
                  }}
                >
                  Reject
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </TabsContent>

      <TabsContent value="activity" className="mt-4 space-y-3">
        {loaded && decided.length === 0 && (
          <p className="py-12 text-center font-mono text-xs tracking-widest text-muted-foreground">
            NO DECISIONS YET
          </p>
        )}
        {decided.map((d) => (
          <Card key={d.id}>
            <CardContent className="space-y-2 py-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-medium">{d.lead_name}</span>
                {d.status === "approved" ? (
                  <Badge className="bg-primary text-primary-foreground font-mono text-[10px]">
                    SENT ✓
                  </Badge>
                ) : (
                  <Badge variant="destructive" className="font-mono text-[10px]">
                    REJECTED
                  </Badge>
                )}
                {d.selected_variant !== null ? (
                  <Badge variant="outline" className="font-mono text-[10px]">
                    ALT #{d.selected_variant + 1} CHOSEN
                  </Badge>
                ) : (
                  d.final_text &&
                  d.final_text !== d.draft && (
                    <Badge variant="outline" className="font-mono text-[10px]">
                      EDITED
                    </Badge>
                  )
                )}
                {d.priority === 1 && d.decided_at && (
                  <Badge variant="outline" className="border-primary/50 font-mono text-[10px] text-primary">
                    ⚡ HANDOFF {fmtMs(d.decided_at - d.created_at)}
                  </Badge>
                )}
                <span className="ml-auto font-mono text-xs text-muted-foreground">
                  {d.decided_at ? timeAgo(d.decided_at) : ""}
                </span>
              </div>
              <p
                className={
                  d.status === "approved"
                    ? "text-sm leading-relaxed"
                    : "text-sm leading-relaxed text-muted-foreground line-through"
                }
              >
                {d.final_text ?? d.draft}
              </p>
              <p className="font-mono text-[11px] text-muted-foreground">
                by {d.decided_by ?? "—"}
                {d.reason ? <> · reason: {d.reason}</> : null}
              </p>
            </CardContent>
          </Card>
        ))}
      </TabsContent>

      <Dialog open={editing !== null} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit before sending</DialogTitle>
          </DialogHeader>
          <Textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            rows={6}
            className="text-base"
          />
          <Textarea
            value={editReason}
            onChange={(e) => setEditReason(e.target.value)}
            rows={2}
            placeholder="What was wrong with the draft? (optional — teaches the agent)"
            className="text-sm"
          />
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button
              disabled={!editText.trim() || busy === editing?.id}
              onClick={() =>
                editing &&
                decide(editing, "approve", editText.trim(), editReason.trim() || undefined)
              }
            >
              Approve &amp; send
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rejecting !== null} onOpenChange={(open) => !open && setRejecting(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Reject this draft</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Nothing will be sent to the lead. The rejection and your reason are recorded.
          </p>
          <Textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={2}
            placeholder="Why? (optional — e.g. wrong unit, bad tone, outdated price)"
            className="text-sm"
          />
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setRejecting(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={busy === rejecting?.id}
              onClick={() =>
                rejecting &&
                decide(rejecting, "reject", undefined, rejectReason.trim() || undefined)
              }
            >
              Reject draft
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Tabs>
    </div>
  );
}
