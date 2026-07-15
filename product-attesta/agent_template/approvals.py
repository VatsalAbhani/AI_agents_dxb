"""
Remote approver — connects the agent to the Leadcode Guard approval dashboard.

The dashboard (dashboard/ in this repo, Next.js) holds the queue; a manager
approves, edits, or rejects from their phone. This client implements the
Gateway `approver` contract over HTTP with zero dependencies:

    approver(draft, context) -> {"decision": "approve"|"reject", "final": str, "by": str}

Behaviour:
  * POST the draft (+ lead context) to the dashboard, then poll for a decision.
  * FAIL CLOSED: on timeout or any network error the draft is REJECTED —
    an unreviewed message must never be sent because a server hiccuped.

Usage:
    from agent_template.approvals import remote_approver
    agent = ConversationalAgent(config, approver=remote_approver(
        "http://localhost:3005", client="ABC Real Estate"))
"""
import json
import time
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 180.0   # seconds a draft may wait for a human
DEFAULT_POLL = 2.0        # seconds between decision checks


def _request(method, url, api_key, body=None, timeout=15):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "content-type": "application/json", "x-api-key": api_key,
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def remote_approver(base_url, api_key="demo-key", client="demo", channel="whatsapp",
                    timeout=DEFAULT_TIMEOUT, poll_every=DEFAULT_POLL, quiet=False):
    """Build a Gateway-compatible approver backed by the approval dashboard."""
    base = base_url.rstrip("/")

    def approver(draft, context):
        try:
            created = _request("POST", base + "/api/drafts", api_key, {
                "draft": draft,
                "client": client,
                "channel": channel,
                "lead": (context or {}).get("lead") or {},
            })
            draft_id = created["id"]
        except (urllib.error.URLError, OSError, KeyError, ValueError) as ex:
            return {"decision": "reject", "by": f"approval-unreachable ({ex.__class__.__name__}) — fail closed"}

        if not quiet:
            print(f"    [approval] waiting for manager decision on {base}/approvals …")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                r = _request("GET", f"{base}/api/drafts/{draft_id}", api_key)
            except (urllib.error.URLError, OSError, ValueError):
                time.sleep(poll_every)
                continue
            if r.get("status") == "approved":
                return {"decision": "approve",
                        "final": r.get("final") or draft,
                        "by": r.get("by") or "Manager"}
            if r.get("status") == "rejected":
                return {"decision": "reject", "by": r.get("by") or "Manager"}
            time.sleep(poll_every)

        return {"decision": "reject", "by": "approval-timeout — fail closed"}

    return approver
