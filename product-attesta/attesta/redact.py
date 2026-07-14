"""
Attesta — PII redaction.

A minimal, dependency-free redactor for what gets *stored* in the ledger. It
masks obvious personal data (emails, UAE phone numbers, Emirates IDs, long ID
numbers). Integrity hashes in the recorder are computed over the ORIGINAL input,
so redaction never breaks verification or replay-divergence detection.

Production would extend this with named-entity redaction, per-field policies,
tokenization/encryption-at-rest, and re-identification controls.
"""
import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_EID = re.compile(r"\b784-?\d{4}-?\d{7}-?\d\b")
_PHONE = re.compile(r"\+?\d[\d\s\-]{7,}\d")
_LONGID = re.compile(r"\b(?=[A-Z0-9\-]*\d)[A-Z0-9]{7,}\b")


def redact_pii(s):
    """Mask common PII in a string. Non-strings pass through unchanged."""
    if not isinstance(s, str):
        return s
    s = _EMAIL.sub("[email]", s)
    s = _EID.sub("[emirates-id]", s)      # before phone: EID also looks phone-like
    s = _PHONE.sub("[phone]", s)
    s = _LONGID.sub("[id]", s)
    return s
