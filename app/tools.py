from __future__ import annotations
from datetime import datetime

from . import ittools
from . import evtools

class ToolRegistry:
    def __init__(self, business: dict, store):
        self.business = business
        self.store = store

    def descriptions(self):
        base = {
            "create_support_ticket": "Create a support ticket when the customer needs a human or unresolved action. args: reason, summary",
            "request_callback": "Record a callback request. args: name, phone, reason",
            "check_business_hours": "Return configured business hours. args: none",
            "get_order_status": "Demo order lookup. args: order_id. Replace with Shopify/ERP adapter.",
            "book_slot": "Demo booking request. args: date, time, service. Replace with calendar/FSM adapter.",
        }
        base.update(ittools.DESCRIPTIONS)
        base.update(evtools.DESCRIPTIONS)
        return base

    def call(self, name: str, args: dict, session_id: str):
        if name in evtools.DESCRIPTIONS:
            if name == "qualify_lead":
                res = evtools.qualify_lead(args)
            elif name == "triage_urgency":
                res = evtools.triage_urgency(
                    args.get("message", ""),
                    args.get("hour"),
                    bool(args.get("vulnerable", False)))
            elif name == "book_survey":
                res = evtools.book_survey(args)
            else:
                res = {"ok": False, "error": f"unknown tool: {name}"}
            ittools.audit(session_id, name,
                          res.get("tier", "safe"), args, res)
            return res
        if name in ittools.DESCRIPTIONS:
            if name in ittools.SAFE:
                res = ittools.diagnose(name, args)
            elif name == "propose_fix":
                res = ittools.propose(session_id, args.get("action", ""),
                                      {k: v for k, v in args.items() if k != "action"})
            elif name == "execute_fix":
                res = ittools.execute(session_id, args.get("confirm_token", ""),
                                      args.get("idempotency_key", ""))
            else:
                res = {"ok": False, "error": f"unknown tool: {name}"}
            ittools.audit(session_id, name,
                          res.get("tier", "safe"), args, res)
            return res
        if name == "create_support_ticket":
            tid = self.store.create_ticket(session_id, "support", args)
            return {"ok": True, "ticket_id": tid}
        if name == "request_callback":
            tid = self.store.create_ticket(session_id, "callback", args)
            return {"ok": True, "ticket_id": tid, "message": "Callback request recorded."}
        if name == "check_business_hours":
            return {"ok": True, "hours": self.business.get("business", {}).get("hours", {})}
        if name == "get_order_status":
            oid = str(args.get("order_id", "")).strip()
            return {"ok": True, "order_id": oid, "status": "demo_only", "message": "Connect tools/shopify.py or your ERP for live status."}
        if name == "book_slot":
            tid = self.store.create_ticket(session_id, "booking", args)
            return {"ok": True, "booking_request": tid, "status": "pending_confirmation"}
        return {"ok": False, "error": f"unknown tool: {name}"}
