"""
Attesta — the tamper-evident ledger.

Every agent action is appended as a hash-chained entry: each entry commits to
the hash of the previous one, so any later edit breaks the chain. At the end of
a run the ledger is sealed with a Merkle root and a signature, giving an
tamper-evident fingerprint of the whole run.

v0 uses HMAC-SHA256 for the seal signature so the demo runs with zero
dependencies. Production swaps this for asymmetric signing (KMS / Sigstore) and
anchors the Merkle root to a public transparency log (RFC 3161 / Rekor).
"""
import hashlib
import hmac
import json
import time

GENESIS = "0" * 64


def canon(obj) -> str:
    """Deterministic JSON so hashes are stable across machines."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# fields that are covered by the tamper-evident hash
_HASHED = ("seq", "type", "name", "payload", "prev_hash", "ts")


def _entry_hash(rec: dict) -> str:
    return sha(canon({k: rec[k] for k in _HASHED}))


class Ledger:
    def __init__(self):
        self.entries = []
        self.sealed = None

    @property
    def head(self) -> str:
        return self.entries[-1]["entry_hash"] if self.entries else GENESIS

    def append(self, etype: str, name: str, payload: dict) -> dict:
        rec = {
            "seq": len(self.entries),
            "type": etype,
            "name": name,
            "payload": payload,
            "prev_hash": self.head,
            "ts": time.time(),
        }
        rec["entry_hash"] = _entry_hash(rec)
        self.entries.append(rec)
        return rec

    def merkle_root(self) -> str:
        hashes = [e["entry_hash"] for e in self.entries]
        if not hashes:
            return GENESIS
        while len(hashes) > 1:
            if len(hashes) % 2:
                hashes.append(hashes[-1])
            hashes = [sha(hashes[i] + hashes[i + 1]) for i in range(0, len(hashes), 2)]
        return hashes[0]

    def seal(self, key: str = None) -> dict:
        root = self.merkle_root()
        seal = {"merkle_root": root, "count": len(self.entries), "sealed_at": time.time()}
        if key:
            seal["alg"] = "HMAC-SHA256"
            seal["signature"] = hmac.new(
                key.encode(), (root + str(len(self.entries))).encode(), hashlib.sha256
            ).hexdigest()
        self.sealed = seal
        return seal

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(canon(e) + "\n")
            if self.sealed:
                f.write(canon({"_seal": self.sealed}) + "\n")

    @staticmethod
    def load(path: str) -> "Ledger":
        led = Ledger()
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if "_seal" in obj:
                    led.sealed = obj["_seal"]
                else:
                    led.entries.append(obj)
        return led


# exported for the verifier so recompute logic lives in one place
def recompute_entry_hash(rec: dict) -> str:
    return _entry_hash(rec)
