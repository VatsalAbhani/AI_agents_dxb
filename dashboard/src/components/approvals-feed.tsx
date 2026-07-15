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
};

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
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [p, d] = await Promise.all([
        fetch("/api/drafts?status=pending").then((r) => r.json()),
        fetch("/api/drafts?status=decided").then((r) => r.json()),
      ]);
      setPending(p.drafts ?? []);
      setDecided(d.drafts ?? []);
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

  async function decide(
    d: Draft,
    decision: "approve" | "reject",
    finalText?: string
  ) {
    setBusy(d.id);
    try {
      const res = await fetch(`/api/drafts/${d.id}/decide`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision, final: finalText, by: "Manager" }),
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
          return (
            <Card key={d.id} className="overflow-hidden">
              <CardHeader className="pb-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-base font-semibold">{d.lead_name}</span>
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
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="outline"
                  className="h-12 text-destructive hover:text-destructive"
                  disabled={busy === d.id}
                  onClick={() => decide(d, "reject")}
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
                {d.final_text && d.final_text !== d.draft && (
                  <Badge variant="outline" className="font-mono text-[10px]">
                    EDITED
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
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button
              disabled={!editText.trim() || busy === editing?.id}
              onClick={() => editing && decide(editing, "approve", editText.trim())}
            >
              Approve &amp; send
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Tabs>
  );
}
