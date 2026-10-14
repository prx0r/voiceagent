from __future__ import annotations
from datetime import datetime

from . import ittools

class ToolRegistry:
    def __init__(self, business: dict, store):
        self.business = business
        self.store = store

    def descriptions(self):
        base = {
            "create_support_ticket": "Create a support ticket when the customer needs a human or unresolved action. args: reason, summary",
            "request_callback": "Record a callback request AND queue a nagging reminder. args: name, phone, reason",
            "check_business_hours": "Return configured business hours. args: none",
            "get_order_status": "Demo order lookup. args: order_id. Replace with Shopify/ERP adapter.",
            "book_slot": "Book an appointment: propose free slots when date/time absent, confirm when present. args: date, time, service, name, phone, email",
        }
        base.update(ittools.DESCRIPTIONS)
        return base

    def call(self, name: str, args: dict, session_id: str):
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
            import sys as _s, os as _o
            _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
            from afterhours import queue_reminder
            biz = (self.business.get("business", {}) or {}).get("name", "")
            queue_reminder(str(args.get("name", "")), str(args.get("phone", "")),
                           f"callback: {args.get('reason', '')}", "standard", biz)
            tid = self.store.create_ticket(session_id, "callback", args)
            return {"ok": True, "ticket_id": tid, "message": "Callback request recorded and reminder queued."}
        if name == "check_business_hours":
            return {"ok": True, "hours": self.business.get("business", {}).get("hours", {})}
        if name == "get_order_status":
            oid = str(args.get("order_id", "")).strip()
            return {"ok": True, "order_id": oid, "status": "demo_only", "message": "Connect tools/shopify.py or your ERP for live status."}
        if name == "book_slot":
            import sys as _s, os as _o
            _s.path.insert(0, _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))))
            import booking as booking_engine
            biz = (self.business.get("business", {}) or {}).get("name", "")
            if not args.get("date") or not args.get("time"):
                return {"ok": True, "needs_pick": True,
                        "days": booking_engine.propose()}
            return booking_engine.confirm(
                biz, str(args.get("name", "")), str(args.get("phone", "")),
                str(args.get("email", "")), str(args.get("service", "")),
                str(args.get("date", "")), str(args.get("time", "")))
        return {"ok": False, "error": f"unknown tool: {name}"}
