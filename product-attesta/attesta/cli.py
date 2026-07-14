"""
Attesta CLI:  attesta verify <ledger>   ·   attesta show <ledger>
"""
import argparse
import json
import sys

from .ledger import Ledger
from .verifier import verify


def cmd_verify(a) -> int:
    r = verify(a.ledger, key=a.key)
    print(json.dumps({k: v for k, v in r.items() if k != "problems"}, indent=2))
    if r["problems"]:
        print("\nproblems:")
        for p in r["problems"]:
            print(f"  · entry #{p['seq']}: {p['issue']}")
    print("\nRESULT:", "✓ INTACT — authentic and untampered"
          if r["intact"] else "✗ TAMPERED — integrity check FAILED")
    return 0 if r["intact"] else 1


def cmd_show(a) -> int:
    led = Ledger.load(a.ledger)
    for e in led.entries:
        p = e.get("payload", {})
        inp = json.dumps(p.get("input"))
        out = json.dumps(p.get("output"))
        print(f"#{e['seq']:>2} {e['type']:>7}:{e['name']:<14} "
              f"in={inp[:52]:<52} out={out[:60]}")
    if led.sealed:
        print("\nseal:", json.dumps(led.sealed))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="attesta", description="Flight recorder for AI agents")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="verify a ledger's integrity offline")
    v.add_argument("ledger")
    v.add_argument("--key", default=None, help="seal signing key (optional)")
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("show", help="pretty-print a recorded run")
    s.add_argument("ledger")
    s.set_defaults(func=cmd_show)

    a = ap.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
