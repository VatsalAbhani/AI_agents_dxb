"""
Attesta — the offline verifier.

Given a ledger file (and optionally the seal key), recompute the entire
hash-chain and Merkle root and confirm nothing was altered. This is the trust-
minimizing core: anyone can verify a run's integrity without trusting Attesta's
servers.
"""
import hashlib
import hmac

from .ledger import Ledger, GENESIS, recompute_entry_hash


def verify(path: str, key: str = None) -> dict:
    led = Ledger.load(path)
    problems = []
    prev = GENESIS

    for e in led.entries:
        # 1) content integrity: does the stored hash still match the content?
        if recompute_entry_hash(e) != e.get("entry_hash"):
            problems.append({"seq": e.get("seq"), "issue": "entry content was altered (hash mismatch)"})
        # 2) chain integrity: does each entry point at the real previous hash?
        if e.get("prev_hash") != prev:
            problems.append({"seq": e.get("seq"), "issue": "broken chain link (an entry was inserted/removed/reordered)"})
        prev = e.get("entry_hash")

    root = led.merkle_root()
    result = {
        "entries": len(led.entries),
        "chain_ok": len(problems) == 0,
        "problems": problems,
        "merkle_root": root,
    }

    if led.sealed:
        result["sealed_root"] = led.sealed.get("merkle_root")
        result["root_matches_seal"] = (root == led.sealed.get("merkle_root"))
        if key and "signature" in led.sealed:
            expect = hmac.new(
                key.encode(),
                (led.sealed["merkle_root"] + str(led.sealed["count"])).encode(),
                hashlib.sha256,
            ).hexdigest()
            result["signature_valid"] = (expect == led.sealed["signature"])

    result["intact"] = (
        result["chain_ok"]
        and result.get("root_matches_seal", True)
        and result.get("signature_valid", True) is not False
    )
    return result
