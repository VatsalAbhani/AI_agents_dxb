"""
Attesta live demo — run:  python examples/demo_agent.py

Records a tiny non-deterministic "agent", then shows the four things Attesta does
that plain logging/tracing can't:
  [1] RECORD    a run into a tamper-evident ledger
  [2] VERIFY    the ledger offline (no server, no trust)
  [3] REPLAY    the exact run and reproduce it
  [4] CATCH     tampering (edited ledger) and code-drift (agent changed)
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from attesta.ledger import Ledger          # noqa: E402
from attesta.recorder import Recorder      # noqa: E402
from attesta.replay import replay          # noqa: E402
from attesta.verifier import verify        # noqa: E402

KEY = "demo-signing-key"        # prod: KMS / asymmetric key + Sigstore anchor
LEDGER = "run.attesta.jsonl"
TAMPERED = "run.tampered.jsonl"


# ---- a tiny, non-deterministic "agent" ------------------------------
def fake_llm(prompt):
    return random.choice(["check weather then advise", "advise directly", "ask a question"])


def weather_api(city):
    return {"city": city, "tempC": random.randint(18, 44)}


def run_agent(rec: Recorder, goal, city, style="normal"):
    """Any agent works if it routes non-determinism through `rec`."""
    ts = rec.now()
    plan = rec.llm("planner", fake_llm, f"goal={goal}")
    weather = rec.tool("get_weather", weather_api, city)
    if style == "extra_step":                     # simulate an added line of code
        rec.tool("get_weather", weather_api, city)
    city_arg = city if style != "changed_input" else city + "!"   # simulate a changed input
    advice = rec.llm("writer", fake_llm, f"plan={plan};weather={weather};city={city_arg}")
    return {"ts": ts, "plan": plan, "weather": weather, "advice": advice}


def tamper(src, dst):
    """Forge a recorded tool output — the kind of edit Attesta must catch."""
    lines = [l for l in open(src).read().splitlines() if l.strip()]
    out, done = [], False
    for l in lines:
        o = json.loads(l)
        if not done and o.get("type") == "tool":
            o["payload"]["output"]["tempC"] = 999      # rewrite history
            done = True
        out.append(json.dumps(o, sort_keys=True, separators=(",", ":")))
    open(dst, "w").write("\n".join(out) + "\n")


def line():
    print("-" * 68)


def main():
    print("=" * 68)
    print("  ATTESTA — the flight recorder for AI agents · live demo")
    print("=" * 68)

    # [1] RECORD
    random.seed(7)                       # only so the demo's 'live' run is stable to read
    rec = Recorder("record")
    result = run_agent(rec, goal="Should I go outside?", city="Dubai")
    rec.ledger.seal(KEY)
    rec.ledger.save(LEDGER)
    line()
    print("[1] RECORDED a run:")
    print("    result :", result)
    print(f"    ledger : {len(rec.ledger.entries)} entries · merkle={rec.ledger.merkle_root()[:20]}...")

    # [2] VERIFY
    line()
    print("[2] VERIFY offline (anyone can, without trusting us):")
    v = verify(LEDGER, key=KEY)
    print(f"    chain_ok={v['chain_ok']}  root_matches_seal={v['root_matches_seal']}  "
          f"signature_valid={v.get('signature_valid')}  ->  {'INTACT ✓' if v['intact'] else 'FAIL'}")

    # [3] REPLAY
    line()
    print("[3] REPLAY the exact run against the recording:")
    rep = replay(run_agent, Ledger.load(LEDGER), goal="Should I go outside?", city="Dubai", sign_key=KEY)
    print(f"    reproduced={rep['reproduced']}  steps={rep['steps']}  "
          f"->  {'REPRODUCED ✓ (signed)' if rep['reproduced'] else 'DIVERGED'}")

    # [4a] TAMPER
    line()
    print("[4a] Someone edits the ledger (forges the recorded temperature to 999)...")
    tamper(LEDGER, TAMPERED)
    vt = verify(TAMPERED, key=KEY)
    print(f"    intact={vt['intact']}  ->  {'TAMPER DETECTED ✓' if not vt['intact'] else 'not detected'}")
    if vt["problems"]:
        print(f"    problem: entry #{vt['problems'][0]['seq']} — {vt['problems'][0]['issue']}")

    # [4b] CODE-DRIFT
    line()
    print("[4b] The agent code changes, then we replay the OLD ledger:")
    d1 = replay(run_agent, Ledger.load(LEDGER), goal="Should I go outside?", city="Dubai", style="extra_step")
    d2 = replay(run_agent, Ledger.load(LEDGER), goal="Should I go outside?", city="Dubai", style="changed_input")
    for d in (d1["divergences"] + d2["divergences"]):
        print(f"    · DIVERGENCE [{d['kind']}] — {d['detail']}")

    line()
    print("record → verify → replay → catch tampering → catch code drift.")
    print("All local. Zero dependencies. This is the v0 core.")
    print("=" * 68)


if __name__ == "__main__":
    main()
