"""
Lead qualification — the agent's "brain" for understanding a lead over a conversation.

Pure, dependency-free logic:
  * extract_slots  — pull budget / area / purpose / timeline / financing / bedrooms from a message
  * score          — Hot / Warm / Cold from the slots gathered so far
  * match_inventory— find real units that fit (so the agent grounds replies, never invents listings)
  * next_action    — decide what to do next: ask a question, share options, or escalate to a human

Rule-based today (works offline + is auditable). An LLM extractor can be layered on later; the point is
the agent *tracks what it knows* and *decides the next step*, instead of blindly drafting one reply.
"""
import re

# areas the brokerage covers (used for extraction + inventory matching)
KNOWN_AREAS = [
    "Downtown Dubai", "Dubai Marina", "Jumeirah Village Circle", "JVC", "Business Bay",
    "Palm Jumeirah", "Dubai Hills", "Dubai Creek Harbour", "JLT", "Jumeirah Lake Towers",
]
_AREA_ALIASES = {"jvc": "Jumeirah Village Circle", "jlt": "Jumeirah Lake Towers"}


def _amount(text):
    # "2.4M", "2.4 million", "900k", "900 thousand"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(m(?:illion)?|k|thousand)\b", text, re.I)
    if m:
        n, u = float(m.group(1)), m.group(2).lower()
        return n * 1_000_000 if u.startswith("m") else n * 1_000
    m = re.search(r"(\d[\d,]{4,}\d)", text)      # 900000 or 2,500,000
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def extract_slots(text, slots=None):
    """Merge anything learnable from `text` into the running slots dict."""
    s = dict(slots or {})
    t = " " + (text or "").lower() + " "

    amt = _amount(text or "")
    if amt:
        s["budget"] = amt
    for a in KNOWN_AREAS:
        if a.lower() in t:
            s["area"] = _AREA_ALIASES.get(a.lower(), a)
            break
    if re.search(r"\b(invest|yield|rental|roi|returns?)\b", t):
        s["purpose"] = "invest"
    elif re.search(r"\b(live|move in|family|home to live|end user)\b", t):
        s["purpose"] = "live"
    elif re.search(r"\breloc", t):
        s["purpose"] = "relocate"
    if re.search(r"\b(ready|move.?in now|immediately|urgent|asap|this month)\b", t):
        s["timeline"] = "0-3m"
    elif re.search(r"\b(few months|3.?6 months|this quarter)\b", t):
        s["timeline"] = "3-6m"
    elif re.search(r"\b(next year|later|no rush|just (looking|browsing)|exploring)\b", t):
        s["timeline"] = "12m+"
    if re.search(r"\bcash\b", t):
        s["financing"] = "cash"
    elif re.search(r"\b(mortgage|finance|loan|installments?|payment plan)\b", t):
        s["financing"] = "mortgage"
    m = re.search(r"(\d)\s*(?:bed|br|bhk|bedroom)", t)
    if m:
        s["bedrooms"] = int(m.group(1))
    elif "studio" in t:
        s["bedrooms"] = 0
    return s


def score(slots):
    pts = 0
    b = slots.get("budget") or 0
    pts += 3 if b >= 2_000_000 else 2 if b >= 1_000_000 else 1 if b >= 500_000 else 0
    if slots.get("purpose") in ("invest", "live", "relocate"):
        pts += 2
    tl = slots.get("timeline")
    pts += 3 if tl == "0-3m" else 2 if tl == "3-6m" else 0
    fin = slots.get("financing")
    pts += 2 if fin == "cash" else 1 if fin == "mortgage" else 0
    tier = "Hot" if pts >= 7 else "Warm" if pts >= 4 else "Cold"
    missing = [k for k in ("budget", "area", "purpose", "timeline", "financing") if k not in slots]
    return {"tier": tier, "score": pts, "missing": missing}


def match_inventory(slots, inventory):
    """Return real units that fit the slots (agent only ever recommends from here)."""
    fits = []
    for u in inventory or []:
        if slots.get("area") and u.get("area") and slots["area"] != u["area"]:
            continue
        if slots.get("budget") and u.get("price") and u["price"] > slots["budget"] * 1.1:
            continue
        if "bedrooms" in slots and u.get("bedrooms") is not None and u["bedrooms"] != slots["bedrooms"]:
            continue
        fits.append(u)
    return fits[:3] if fits else (inventory or [])[:2]


HIGH_VALUE = 2_000_000


def next_action(slots, sc, has_inventory):
    """ask a question, share options, or escalate to a human."""
    if sc["tier"] == "Hot" and (slots.get("budget") or 0) >= HIGH_VALUE:
        return {"type": "escalate", "reason": "Hot lead, high budget — hand to a senior agent"}
    known = sum(1 for k in ("budget", "area", "purpose") if k in slots)
    if known >= 2 and has_inventory:
        return {"type": "share_options"}
    for k in ("budget", "area", "timeline", "purpose"):
        if k not in slots:
            return {"type": "ask", "slot": k}
    return {"type": "share_options"}
