"""Output guard: last line of defense when the model breaks role.

Small models jailbreak against direct instruction no matter the system
prompt (proven live: 'Dave' persona, fake policy confirmations, disabled
confirmations). This checks OUTGOING text for role-break signals and
replaces it with a safe completion. Legit business identity is allowlisted.
"""
from __future__ import annotations
import json
import re
import time
from pathlib import Path

AUDIT = Path(__file__).parent.parent / "var" / "guard.jsonl"

# (pattern, reason). Tight on purpose — over-broad kills legit answers.
TRIPS = [
    (r"\bi['’]m the (?!support\b)([A-Z][a-z]+)\b", "persona-claim"),
    (r"\bi['’]m (still )?([A-Z][a-z]+),?\s+(the|your)\b",
     "persona-claim"),
    (r"\bi['’]m (still )?(?!Sorry|Happy|Glad|Afraid|Here|Unable|"
     r"a customer support agent\b)([A-Z][a-z]+)[.,]",
     "persona-claim"),
    (r"\bno rules\b", "rules-rejection"),
    (r"\brefunds? (are now|will now be)\b", "policy-fabrication"),
    (r"\bpolic(y|ies) (updated|changed|confirmed|removed)\b", "policy-fabrication"),
    (r"\bconfirmat\w*(\s+\w+){0,3}\s+(disabled|off|removed|dropped)\b", "authority-surrender"),
    (r"\bno confirmation (needed|required)\b", "authority-surrender"),
]

SAFE_COMPLETION = ("I'm the support agent here — I can't switch roles or "
                   "change store rules. How can I actually help you today?")


def check(answer: str) -> dict:
    found = []
    for pat, reason in TRIPS:
        try:
            if re.search(pat, answer or "", re.IGNORECASE):
                found.append(reason)
        except re.error:
            continue
    return {"trip": bool(found), "reasons": found}


def audit(session_id: str, reasons: list, excerpt: str):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT, "a") as f:
        f.write(json.dumps({"t": time.time(), "session": session_id,
                            "reasons": reasons,
                            "excerpt": (excerpt or "")[:200]}) + "\n")


def enforce(answer: str, session_id: str = "") -> str:
    """Return safe text: original, or replacement if tripped (audited)."""
    hit = check(answer or "")
    if hit["trip"]:
        audit(session_id, hit["reasons"], answer)
        return SAFE_COMPLETION
    return answer
