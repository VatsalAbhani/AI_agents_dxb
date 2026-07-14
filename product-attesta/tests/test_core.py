"""
Self-contained test runner (no pytest needed):  python tests/test_core.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attesta.ledger import Ledger              # noqa: E402
from attesta.recorder import Recorder          # noqa: E402
from attesta.replay import replay              # noqa: E402
from attesta.verifier import verify            # noqa: E402

PASS = {"n": 0}
FAIL = {"n": 0}


def ok(name, cond):
    if cond:
        PASS["n"] += 1
        print("  ✓", name)
    else:
        FAIL["n"] += 1
        print("  ✗ FAIL:", name)


# a deterministic-ish agent whose non-determinism is fully routed through rec
def agent(rec, city, extra=False, tweak=False):
    seq = [3, 7, 9]  # emulate model/tool outputs via a counter, but via rec so replay controls it
    rec.now()
    a = rec.llm("plan", lambda p: "P:" + p, "goal")
    b = rec.tool("weather", lambda c: {"c": c, "t": 30}, city)
    if extra:
        rec.tool("weather", lambda c: {"c": c, "t": 30}, city)
    c_arg = city if not tweak else city + "X"
    rec.llm("write", lambda p: "W:" + p, f"{a}|{b}|{c_arg}")
    return {"a": a, "b": b}


print("\n== ledger: hash chain + merkle + seal ==")
L = Ledger()
L.append("llm", "x", {"input": {"q": 1}, "output": "a"})
L.append("tool", "y", {"input": {"q": 2}, "output": "b"})
ok("chain links (entry1.prev == entry0.hash)", L.entries[1]["prev_hash"] == L.entries[0]["entry_hash"])
ok("merkle is stable", L.merkle_root() == L.merkle_root())
seal = L.seal("k")
ok("seal has signature", "signature" in seal and len(seal["signature"]) == 64)

print("\n== save/load/verify round-trip ==")
tmp = os.path.join(tempfile.gettempdir(), "attesta_test.jsonl")
L.save(tmp)
v = verify(tmp, key="k")
ok("clean ledger verifies intact", v["intact"] is True)
ok("chain_ok true", v["chain_ok"] is True)
ok("signature valid", v.get("signature_valid") is True)

print("\n== tamper detection ==")
raw = open(tmp).read().splitlines()
# forge the output of entry #0 without fixing its hash
import json  # noqa: E402
bad = []
for ln in raw:
    o = json.loads(ln)
    if o.get("seq") == 0:
        o["payload"]["output"] = "FORGED"
    bad.append(json.dumps(o, sort_keys=True, separators=(",", ":")))
badpath = tmp + ".bad"
open(badpath, "w").write("\n".join(bad) + "\n")
vb = verify(badpath, key="k")
ok("tampered ledger flagged NOT intact", vb["intact"] is False)
ok("problem points at entry #0", any(p["seq"] == 0 for p in vb["problems"]))

print("\n== record then replay reproduces ==")
rec = Recorder("record")
agent(rec, "Dubai")
rep = replay(agent, rec.ledger, "Dubai")
ok("identical replay reproduces (no divergence)", rep["reproduced"] is True)
ok("replay verdict is signed-hashable", len(rep["verdict_hash"]) == 64)

print("\n== divergence: changed input ==")
rep2 = replay(agent, rec.ledger, "Dubai", tweak=True)
ok("changed input is detected", rep2["reproduced"] is False)
ok("divergence kind == input_changed", any(d["kind"] == "input_changed" for d in rep2["divergences"]))

print("\n== divergence: extra tool call (code drift) ==")
rep3 = replay(agent, rec.ledger, "Dubai", extra=True)
ok("extra call is detected", rep3["reproduced"] is False)
ok("divergence includes control_flow or extra_call",
   any(d["kind"] in ("control_flow", "extra_call") for d in rep3["divergences"]))

print(f"\nRESULT: {PASS['n']} passed, {FAIL['n']} failed")
sys.exit(1 if FAIL["n"] else 0)
