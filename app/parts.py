"""Parts lookup: quotable prices with stock flags. Order needs approval.

Never auto-order. Flow: check() -> propose (approval token) -> approve(token).
Tokens single-use, 24h. Supplier lookup is a stub table today; swap for
real supplier API (City Electrical, Screwfix Trade, TLC) without changing callers.
All pure + file-free except in-memory outstanding tokens (fine for MVP single proc).
"""
from __future__ import annotations
import secrets
import time

# name -> {price, unit, stock, lead_days, supplier}
CATALOG = {
    "ohme_home_pro": {"price": 549, "unit": "each", "stock": True, "lead_days": 2, "supplier": "CEF"},
    "easee_one": {"price": 629, "unit": "each", "stock": True, "lead_days": 2, "supplier": "TLC"},
    "pod_point_solo3": {"price": 599, "unit": "each", "stock": False, "lead_days": 7, "supplier": "CEF"},
    "tesla_wall_connector": {"price": 479, "unit": "each", "stock": True, "lead_days": 3, "supplier": "Screwfix Trade"},
    "zappi_v2": {"price": 699, "unit": "each", "stock": True, "lead_days": 3, "supplier": "TLC"},
    "rcbo_32a_typeA": {"price": 38, "unit": "each", "stock": True, "lead_days": 1, "supplier": "CEF"},
    "mini_consumer_unit": {"price": 85, "unit": "each", "stock": True, "lead_days": 1, "supplier": "CEF"},
    "swa_6mm_per_m": {"price": 6.5, "unit": "m", "stock": True, "lead_days": 1, "supplier": "TLC"},
    "ct_clamp_equaliser": {"price": 65, "unit": "each", "stock": True, "lead_days": 2, "supplier": "TLC"},
}

OUTSTANDING: dict[str, dict] = {}

# Optional live supplier lookup. If SUPPLIER_MCP_URL is set, check() asks it
# first (Storefront-MCP style: POST {"sku","qty"} -> {price, in_stock, lead_days,
# supplier}); anything it doesn't know falls back to CATALOG below. No key =
# pure table, tests and demos unaffected.
import os as _os
SUPPLIER_MCP_URL = _os.getenv("SUPPLIER_MCP_URL", "")


def mcp_lookup(sku: str, qty: float = 1) -> dict | None:
    if not SUPPLIER_MCP_URL:
        return None
    try:
        import httpx
        r = httpx.post(SUPPLIER_MCP_URL, json={"sku": sku, "qty": qty},
                       timeout=8)
        r.raise_for_status()
        d = r.json()
        if "price" not in d:
            return None
        return {"price": float(d["price"]), "unit": d.get("unit", "each"),
                "stock": bool(d.get("in_stock", True)),
                "lead_days": int(d.get("lead_days", 0)),
                "supplier": str(d.get("supplier", "mcp"))}
    except Exception:
        return None


def check(items: list[dict]) -> dict:
    """items: [{sku, qty}]. Returns lines + total + delays."""
    lines, total, delay = [], 0.0, 0
    for it in items or []:
        sku = str(it.get("sku", ""))
        qty = float(it.get("qty", 1) or 1)
        live = mcp_lookup(sku, qty)
        c = live or CATALOG.get(sku)
        if not c:
            return {"ok": False, "error": f"unknown sku: {sku}"}
        lines.append({"sku": sku, "qty": qty, "each": c["price"],
                      "line": round(c["price"] * qty, 2),
                      "in_stock": c["stock"], "lead_days": c["lead_days"],
                      "supplier": c["supplier"]})
        total += c["price"] * qty
        delay = max(delay, 0 if c["stock"] else c["lead_days"])
    return {"ok": True, "tier": "safe", "lines": lines,
            "parts_total": round(total, 2), "delay_days": delay}


def propose(items: list[dict], case_id: str = "") -> dict:
    chk = check(items)
    if not chk.get("ok"):
        return chk
    tok = "parts_" + secrets.token_hex(4)
    OUTSTANDING[tok] = {"items": items, "case": case_id,
                        "expires": time.time() + 86400}
    return {"ok": True, "tier": "moderate", "approval_token": tok,
            "parts_total": chk["parts_total"], "delay_days": chk["delay_days"],
            "message": f"Parts £{chk['parts_total']} reserved. Approve with: {tok}"}


def approve(token: str) -> dict:
    job = OUTSTANDING.pop(token, None)
    if not job or job["expires"] < time.time():
        return {"ok": False, "error": "bad or expired approval token"}
    return {"ok": True, "tier": "moderate", "ordered": job["items"],
            "case": job["case"], "status": "ordered_pending_delivery"}
