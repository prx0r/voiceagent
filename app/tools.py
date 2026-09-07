from __future__ import annotations
from datetime import datetime

class ToolRegistry:
    def __init__(self, business: dict, store):
        self.business = business
        self.store = store

    def descriptions(self):
        return {
            "create_support_ticket": "Create a support ticket when the customer needs a human or unresolved action. args: reason, summary",
            "request_callback": "Record a callback request. args: name, phone, reason",
            "check_business_hours": "Return configured business hours. args: none",
            "get_order_status": "Demo order lookup. args: order_id. Replace with Shopify/ERP adapter.",
            "book_slot": "Demo booking request. args: date, time, service. Replace with calendar/FSM adapter.",
        }

    def call(self, name: str, args: dict, session_id: str):
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
