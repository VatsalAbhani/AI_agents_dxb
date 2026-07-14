"""
Attesta — the recorder (the $1B core).

Wrap the non-deterministic *boundaries* of an agent (LLM calls, tool calls,
time, randomness). RECORD mode calls the real thing and logs the exact
input + output into the tamper-evident ledger. REPLAY mode returns the recorded
output and flags DIVERGENCE — and, critically, NEVER makes a live call, so
replaying can't fire real-world side effects (no rogue WhatsApp/CRM/payment).

Two hardening fixes over v0:
  * side-effect-safe replay: unexpected/extra calls return a sentinel (or raise
    in strict mode) instead of executing live;
  * redaction hook: an optional redactor scrubs PII from what gets *stored*,
    while integrity hashes are computed over the ORIGINAL inputs so verification
    and divergence detection are unaffected.
"""
import random as _random
import time as _time

from .ledger import Ledger, canon, sha


class ReplayDivergence(Exception):
    """Raised in strict replay when the run diverges from the recording."""


# returned (never a live call) when replay hits a call with no recorded match
REPLAY_UNAVAILABLE = {"__attesta__": "replay_unavailable"}


def _walk_redact(value, redactor):
    if redactor is None:
        return value
    if isinstance(value, str):
        return redactor(value)
    if isinstance(value, dict):
        return {k: _walk_redact(v, redactor) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_walk_redact(v, redactor) for v in value]
    return value


class Recorder:
    def __init__(self, mode="record", ledger=None, redactor=None, strict=False):
        assert mode in ("record", "replay"), "mode must be 'record' or 'replay'"
        self.mode = mode
        self.ledger = ledger if ledger is not None else Ledger()
        self.redactor = redactor        # callable(str)->str, applied to STORED payloads only
        self.strict = strict            # replay: raise on first divergence instead of collecting
        self.cursor = 0
        self.divergences = []

    def _store(self, value):
        return _walk_redact(value, self.redactor)

    def _diverge(self, d):
        self.divergences.append(d)
        if self.strict:
            raise ReplayDivergence(d["detail"])

    # -- core boundary -------------------------------------------------
    def call(self, etype, name, fn, *args, **kwargs):
        original_inputs = {"args": list(args), "kwargs": kwargs}
        ihash = sha(canon(original_inputs))   # integrity over ORIGINAL, pre-redaction

        if self.mode == "record":
            out = fn(*args, **kwargs)
            self.ledger.append(etype, name, {
                "input": self._store(original_inputs),
                "input_hash": ihash,
                "output": self._store(out),
            })
            return out  # agent receives the ORIGINAL output; redaction only affects storage

        # ---- replay: never calls fn (side-effect-safe) ----
        entries = self.ledger.entries
        if self.cursor >= len(entries):
            self._diverge({"step": self.cursor, "kind": "extra_call",
                           "detail": f"{etype}:{name} has no recorded counterpart (agent did more than the recording)"})
            return REPLAY_UNAVAILABLE
        e = entries[self.cursor]
        self.cursor += 1
        if e["type"] != etype or e["name"] != name:
            self._diverge({"step": e["seq"], "kind": "control_flow",
                           "detail": f"expected {e['type']}:{e['name']} but agent called {etype}:{name}"})
        if ihash != e["payload"]["input_hash"]:
            self._diverge({"step": e["seq"], "kind": "input_changed",
                           "detail": f"inputs to {name} differ from the recording",
                           "recorded": e["payload"]["input"], "now": self._store(original_inputs)})
        return e["payload"]["output"]  # serve recorded output — still no live call

    # -- non-fn events (policy checks, approvals, gateway decisions) ----
    def event(self, etype, name, payload):
        if self.mode == "record":
            self.ledger.append(etype, name, self._store(payload))
            return payload
        entries = self.ledger.entries
        if self.cursor >= len(entries):
            self._diverge({"step": self.cursor, "kind": "extra_call",
                           "detail": f"event {etype}:{name} not in recording"})
            return REPLAY_UNAVAILABLE
        e = entries[self.cursor]
        self.cursor += 1
        if e["type"] != etype or e["name"] != name:
            self._diverge({"step": e["seq"], "kind": "control_flow",
                           "detail": f"expected {e['type']}:{e['name']}, got {etype}:{name}"})
        return e["payload"]

    # -- ergonomic wrappers -------------------------------------------
    def llm(self, name, fn, *a, **k):
        return self.call("llm", name, fn, *a, **k)

    def tool(self, name, fn, *a, **k):
        return self.call("tool", name, fn, *a, **k)

    def now(self):
        return self.call("time", "now", _time.time)

    def rand(self):
        return self.call("random", "rand", _random.random)

    # -- reporting -----------------------------------------------------
    def report(self):
        return {
            "reproduced": len(self.divergences) == 0,
            "steps": self.cursor if self.mode == "replay" else len(self.ledger.entries),
            "divergences": self.divergences,
        }
