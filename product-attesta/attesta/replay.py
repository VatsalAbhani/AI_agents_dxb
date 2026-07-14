"""
Attesta — the replay engine.

Re-run an agent function against a recorded ledger and return a signed report of
whether it reproduced or diverged. The agent must accept a Recorder as its first
argument and route its non-deterministic calls through it (rec.llm / rec.tool /
rec.now / rec.rand).
"""
import hashlib
import hmac

from .ledger import Ledger, canon, sha
from .recorder import Recorder


def replay(agent_fn, ledger: Ledger, *args, sign_key: str = None, **kwargs) -> dict:
    rec = Recorder(mode="replay", ledger=ledger)
    result = None
    try:
        result = agent_fn(rec, *args, **kwargs)
    except Exception as ex:  # a crash on replay is itself a divergence
        rec.divergences.append({"step": rec.cursor, "kind": "exception", "detail": repr(ex)})

    rep = rec.report()
    rep["result"] = result
    rep["original_merkle_root"] = ledger.merkle_root()
    # sign the replay verdict so the outcome itself is tamper-evident
    verdict = canon({"root": rep["original_merkle_root"], "reproduced": rep["reproduced"],
                     "divergences": len(rep["divergences"])})
    rep["verdict_hash"] = sha(verdict)
    if sign_key:
        rep["verdict_sig"] = hmac.new(sign_key.encode(), verdict.encode(), hashlib.sha256).hexdigest()
    return rep
