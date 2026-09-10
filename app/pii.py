"""Tiered PII redaction. Two tiers because the business NEEDS callback numbers
but must NEVER persist secrets:

- SECRET (passwords, tokens, keys, card numbers): scrubbed EVERYWHERE, including
  the case store. No code path may persist these. Ever.
- CONTACT (phones, emails, postcodes): kept in the case store + chat history
  (callbacks need them), scrubbed from long-lived AUDIT logs, redacted on export.

UK GDPR logic: data minimisation + purpose limitation. Audit keeps session_id for
correlation, never the contact detail itself.
"""
from __future__ import annotations
import re

SECRET_RES = [
    re.compile(r"(?i)(password|passwd|pwd|api[_-]?key|secret|bearer|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)\b(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|xox[bpas]-[A-Za-z0-9-]{8,})"),
    re.compile(r"\b(?:\d[ -]?){13,19}\b"),  # card-number shaped
]
CONTACT_RES = [
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\+?44[\s\d]{9,}|\(?0\d{3,4}\)?[\s\d-]{6,}"),  # UK phones
    re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"),  # UK postcodes
]


def scrub_secrets(text: str) -> str:
    out = text or ""
    for rx in SECRET_RES:
        out = rx.sub("[REDACTED_SECRET]", out)
    return out


def scrub_contacts(text: str) -> str:
    out = text or ""
    for rx in CONTACT_RES:
        out = rx.sub("[REDACTED_CONTACT]", out)
    return out


def scrub_all(text: str) -> str:
    """Audit-log grade: no secrets, no contact details."""
    return scrub_contacts(scrub_secrets(text))
