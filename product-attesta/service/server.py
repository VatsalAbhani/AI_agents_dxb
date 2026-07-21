"""
Leadcode Guard — the agent service. The piece that makes the product real:
a long-running server that takes leads in, runs guarded agent turns, waits for
dashboard approvals, and keeps every conversation's state + evidence chain on
disk so restarts lose nothing. Pure stdlib — deploys anywhere Python runs.

    python3 service/server.py            (from product-attesta/)

Endpoints (x-api-key: SERVICE_API_KEY, default "demo-key"):
    GET  /health                     liveness + config summary
    POST /leads                      {name, client?, phone?, source?, relationship?,
                                      area?, enquiry?, message?} -> {id}
    POST /leads/<id>/message         {text} -> 202 (turn runs in background)
    GET  /leads/<id>                 state + full turn history
    GET  /leads                      recent conversations (ops view)
    POST /leads/<id>/close           seal ledger, verify, write audit report
    GET  /?key=<SERVICE_API_KEY>     manual intake form (pilot ops)

Env: SERVICE_PORT (8600) · SERVICE_API_KEY · DASHBOARD_URL (http://localhost:3005)
     GUARD_API_KEY · CLIENT_NAME · DATA_DIR (./data) · LEDGER_KEY
     APPROVAL_TIMEOUT (180s) · APPROVAL_POLL (2s)
Plus the usual LLM vars (LLM_PROVIDER, ANTHROPIC_API_KEY / OPENAI_API_KEY…).
"""
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_template.approvals import remote_approver                    # noqa: E402
from agent_template.config import realestate_config                     # noqa: E402
from agent_template.conversation import Conversation, ConversationalAgent  # noqa: E402
from agent_template.drafter import drafter_mode, make_variants, resolve_converser  # noqa: E402
from attesta.ledger import Ledger                                       # noqa: E402
from attesta.recorder import Recorder                                   # noqa: E402
from attesta.redact import redact_pii                                   # noqa: E402
from attesta.verifier import verify                                     # noqa: E402
from attesta.report import audit_report                                 # noqa: E402
from service.state import Store                                         # noqa: E402


def _default_remediator(draft, reasons, config):
    return ("I can't promise outcomes, but I'd gladly share current listings "
            "and comparables so you can decide with full information.")


class AgentService:
    """All state + behaviour; the HTTP handler stays thin."""

    def __init__(self, data_dir=None, dashboard_url=None, api_key=None):
        self.data_dir = data_dir or os.getenv("DATA_DIR", "data")
        self.ledger_dir = os.path.join(self.data_dir, "ledgers")
        self.report_dir = os.path.join(self.data_dir, "reports")
        os.makedirs(self.ledger_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        self.store = Store(os.path.join(self.data_dir, "service.db"))
        self.api_key = api_key or os.getenv("SERVICE_API_KEY", "demo-key")
        self.dashboard = (dashboard_url or os.getenv("DASHBOARD_URL", "http://localhost:3005")).rstrip("/")
        self.guard_key = os.getenv("GUARD_API_KEY", "demo-key")
        self.default_client = os.getenv("CLIENT_NAME", "demo")
        self.ledger_key = os.getenv("LEDGER_KEY", "pilot-ledger-key")
        self.approval_timeout = float(os.getenv("APPROVAL_TIMEOUT", "180"))
        self.approval_poll = float(os.getenv("APPROVAL_POLL", "2"))
        self.pool = ThreadPoolExecutor(max_workers=int(os.getenv("WORKERS", "8")))
        self._convo_locks = {}
        self._locks_guard = threading.Lock()

    # -- helpers -------------------------------------------------------
    def _lock_for(self, cid):
        with self._locks_guard:
            if cid not in self._convo_locks:
                self._convo_locks[cid] = threading.Lock()
            return self._convo_locks[cid]

    def _ledger_path(self, cid):
        return os.path.join(self.ledger_dir, f"{cid}.jsonl")

    def _build_agent(self, client, cid):
        cfg = realestate_config(client)
        path = self._ledger_path(cid)
        ledger = Ledger.load(path) if os.path.exists(path) else Ledger()
        rec = Recorder("record", ledger=ledger, redactor=redact_pii)
        return cfg, ConversationalAgent(
            cfg,
            converser=resolve_converser(cfg),
            approver=remote_approver(self.dashboard, api_key=self.guard_key, client=client,
                                     timeout=self.approval_timeout, poll_every=self.approval_poll,
                                     quiet=True, variants=make_variants(cfg)),
            remediator=_default_remediator,
            recorder=rec,
        )

    def _rebuild_convo(self, row):
        return Conversation(
            lead=json.loads(row["lead"]),
            slots=json.loads(row["slots"]),
            history=json.loads(row["history"]),
            tier=row["tier"],
            escalated=bool(row["escalated"]),
        )

    # -- operations ----------------------------------------------------
    def create_lead(self, body):
        lead = {k: body[k] for k in ("name", "phone", "source", "relationship", "area", "enquiry")
                if body.get(k)}
        lead.setdefault("name", "Lead")
        client = body.get("client") or self.default_client
        cid = self.store.create(client, lead)
        first_message = body.get("message") or body.get("enquiry")
        if first_message:
            self.queue_turn(cid, str(first_message))
        return cid

    def queue_turn(self, cid, text):
        self.store.log_turn(cid, "lead", text)
        self.pool.submit(self._run_turn, cid, text)

    def _run_turn(self, cid, text):
        # one turn at a time per conversation; different leads run in parallel
        with self._lock_for(cid):
            try:
                row = self.store.get(cid)
                if not row or row["status"] != "open":
                    return
                cfg, agent = self._build_agent(row["client"], cid)
                convo = self._rebuild_convo(row)
                r = agent.reply(convo, text)
                agent.rec.ledger.save(self._ledger_path(cid))   # evidence survives restarts
                self.store.save_convo(cid, convo, last_turn_status=r["status"])
                self.store.log_turn(cid, "agent", r["reply"] or "", r["status"])
            except Exception as ex:  # fail loud in the log, closed on the wire
                self.store.log_turn(cid, "agent", "", f"error: {ex.__class__.__name__}: {ex}")

    def close_lead(self, cid):
        with self._lock_for(cid):
            row = self.store.get(cid)
            if not row:
                return None
            path = self._ledger_path(cid)
            ledger = Ledger.load(path) if os.path.exists(path) else Ledger()
            ledger.seal(self.ledger_key)
            ledger.save(path)
            v = verify(path, key=self.ledger_key)
            report_path = os.path.join(self.report_dir, f"{cid}.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(audit_report(path, key=self.ledger_key, client=row["client"],
                                     agent="Lead Follow-up Agent", period="pilot"))
            convo = self._rebuild_convo(row)
            self.store.save_convo(cid, convo, status="closed")
            return {"intact": v["intact"], "entries": v["entries"], "report": report_path}

    def lead_state(self, cid):
        row = self.store.get(cid)
        if not row:
            return None
        return {
            "id": row["id"], "client": row["client"], "lead": json.loads(row["lead"]),
            "slots": json.loads(row["slots"]), "tier": row["tier"],
            "escalated": bool(row["escalated"]), "status": row["status"],
            "last_turn_status": row["last_turn_status"],
            "turns": self.store.turns(cid),
        }


INTAKE_FORM = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Guard — new lead</title><style>
body{font-family:ui-monospace,Menlo,monospace;background:#faf8f2;color:#14150f;
max-width:26rem;margin:2rem auto;padding:0 1rem}
h1{font-size:1rem;letter-spacing:.15em}label{display:block;font-size:.7rem;
letter-spacing:.12em;margin:1rem 0 .3rem;color:#55564b}
input,select,textarea{width:100%%;padding:.7rem;border:1px solid #14150f;
background:#fff;font:inherit;box-sizing:border-box}
button{margin-top:1.2rem;width:100%%;padding:.9rem;background:#ff4d00;color:#14150f;
border:1px solid #ff4d00;font:inherit;letter-spacing:.08em;cursor:pointer}
#out{margin-top:1rem;font-size:.75rem;color:#55564b;white-space:pre-wrap}
</style></head><body>
<h1>▚ LEADCODE GUARD · NEW LEAD</h1>
<label>NAME</label><input id="name" autocomplete="off">
<label>PHONE (optional)</label><input id="phone" autocomplete="off">
<label>SOURCE</label><select id="source"><option>WhatsApp</option><option>Website form</option>
<option>Meta Ads</option><option>Bayut</option><option>Property Finder</option><option>Walk-in / call</option></select>
<label>RELATIONSHIP</label><select id="relationship"><option value="new">New enquiry</option>
<option value="returning">Returning client</option><option value="referral">Referral</option></select>
<label>FIRST MESSAGE / ENQUIRY</label><textarea id="message" rows="4"></textarea>
<button onclick="go()">Hand to the agent</button><div id="out"></div>
<script>
async function go(){
  const b={name:name.value,phone:phone.value,source:source.value,
           relationship:relationship.value,message:message.value};
  const r=await fetch('/leads',{method:'POST',headers:{'content-type':'application/json',
    'x-api-key':new URLSearchParams(location.search).get('key')||''},body:JSON.stringify(b)});
  out.textContent=r.ok?'✓ Lead handed to the agent — the draft will appear on the approvals dashboard.'
    :'✗ '+await r.text();
  if(r.ok){name.value=phone.value=message.value='';}
}
</script></body></html>"""


def make_handler(svc):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj, ctype="application/json"):
            body = (json.dumps(obj) if ctype == "application/json" else obj).encode()
            self.send_response(code)
            self.send_header("content-type", ctype)
            self.end_headers()
            self.wfile.write(body)

        def _authed(self):
            return self.headers.get("x-api-key", "") == svc.api_key

        def _body(self):
            try:
                length = int(self.headers.get("content-length", 0))
                return json.loads(self.rfile.read(length)) if length else {}
            except (ValueError, json.JSONDecodeError):
                return None

        def do_GET(self):
            path, _, query = self.path.partition("?")
            if path == "/health":
                return self._send(200, {"ok": True, "drafter": drafter_mode(),
                                        "dashboard": svc.dashboard})
            if path == "/":
                key = dict(p.split("=", 1) for p in query.split("&") if "=" in p).get("key", "")
                if key != svc.api_key:
                    return self._send(403, "Forbidden — open /?key=<SERVICE_API_KEY>", "text/plain")
                return self._send(200, INTAKE_FORM, "text/html")
            if not self._authed():
                return self._send(401, {"error": "invalid api key"})
            if path == "/leads":
                return self._send(200, {"leads": svc.store.list()})
            if path.startswith("/leads/"):
                state = svc.lead_state(path.split("/")[2])
                return self._send(200, state) if state else self._send(404, {"error": "not found"})
            self._send(404, {"error": "not found"})

        def do_POST(self):
            if not self._authed():
                return self._send(401, {"error": "invalid api key"})
            parts = [p for p in self.path.split("?")[0].split("/") if p]
            body = self._body()
            if body is None:
                return self._send(400, {"error": "invalid JSON"})
            if parts == ["leads"]:
                if not (body.get("name") or body.get("message") or body.get("enquiry")):
                    return self._send(400, {"error": "name or message required"})
                return self._send(201, {"id": svc.create_lead(body)})
            if len(parts) == 3 and parts[0] == "leads" and parts[2] == "message":
                if not str(body.get("text", "")).strip():
                    return self._send(400, {"error": "text required"})
                if not svc.store.get(parts[1]):
                    return self._send(404, {"error": "not found"})
                svc.queue_turn(parts[1], str(body["text"]).strip())
                return self._send(202, {"queued": True})
            if len(parts) == 3 and parts[0] == "leads" and parts[2] == "close":
                result = svc.close_lead(parts[1])
                return self._send(200, result) if result else self._send(404, {"error": "not found"})
            self._send(404, {"error": "not found"})

        def log_message(self, fmt, *args):
            sys.stderr.write("[service] %s\n" % (fmt % args))

    return Handler


def create_server(port=0, **svc_kwargs):
    svc = AgentService(**svc_kwargs)
    server = ThreadingHTTPServer(("0.0.0.0", port), make_handler(svc))
    server.service = svc
    return server


if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8600"))
    srv = create_server(port=port)
    print("=" * 64)
    print("  LEADCODE GUARD · agent service")
    print(f"  port {port} · dashboard {srv.service.dashboard}")
    print(f"  [AI mode] {drafter_mode()}")
    print(f"  intake form: http://localhost:{port}/?key={srv.service.api_key}")
    print("=" * 64)
    srv.serve_forever()
