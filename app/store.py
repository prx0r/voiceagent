from __future__ import annotations
import json, os, sqlite3, time, uuid
from .pii import scrub_secrets

class Store:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("""CREATE TABLE IF NOT EXISTS messages(
          id TEXT PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, ts REAL, meta TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS tickets(
          id TEXT PRIMARY KEY, session_id TEXT, kind TEXT, status TEXT, payload TEXT, ts REAL)""")
        self.db.commit()

    def add_message(self, session_id, role, content, meta=None):
        # Secrets never persist; contact PII stays (callbacks need it) but is
        # TTL-swept with the DB. See app/pii.py for the tiering rationale.
        content = scrub_secrets(content)
        meta = json.loads(scrub_secrets(json.dumps(meta or {})))
        self.db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?)", (str(uuid.uuid4()), session_id, role, content, time.time(), json.dumps(meta)))
        self.db.commit()

    def history(self, session_id, limit=12):
        cur = self.db.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY ts DESC LIMIT ?", (session_id, limit))
        return [dict(role=r, content=c) for r,c in reversed(cur.fetchall())]

    def create_ticket(self, session_id, kind, payload):
        tid = f"T-{uuid.uuid4().hex[:8].upper()}"
        payload = json.loads(scrub_secrets(json.dumps(payload)))
        self.db.execute("INSERT INTO tickets VALUES(?,?,?,?,?,?)", (tid, session_id, kind, "open", json.dumps(payload), time.time()))
        self.db.commit()
        return tid
