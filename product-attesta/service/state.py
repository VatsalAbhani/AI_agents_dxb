"""
Agent service — persistent conversation state (stdlib sqlite3, thread-safe).

Each lead has one conversation row (qualification state + history) and a
per-conversation Attesta ledger file on disk. The service can restart at any
point: state reloads from here, the evidence chain reloads from the ledger.
"""
import json
import os
import sqlite3
import threading
import time
import uuid


class Store:
    def __init__(self, path):
        d = os.path.dirname(os.path.abspath(path))
        os.makedirs(d, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                client TEXT NOT NULL,
                lead TEXT NOT NULL,            -- JSON
                slots TEXT NOT NULL DEFAULT '{}',
                history TEXT NOT NULL DEFAULT '[]',
                tier TEXT NOT NULL DEFAULT 'Cold',
                escalated INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'open',   -- open | closed
                last_turn_status TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )""")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS turns (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                convo_id TEXT NOT NULL,
                role TEXT NOT NULL,            -- lead | agent
                text TEXT NOT NULL,
                status TEXT,                   -- sent | rejected | blocked | …
                ts REAL NOT NULL
            )""")
        self._db.commit()

    def create(self, client, lead):
        cid = str(uuid.uuid4())
        now = time.time()
        with self._lock:
            self._db.execute(
                "INSERT INTO conversations (id, client, lead, created_at, updated_at) VALUES (?,?,?,?,?)",
                (cid, client, json.dumps(lead), now, now))
            self._db.commit()
        return cid

    def get(self, cid):
        with self._lock:
            row = self._db.execute("SELECT * FROM conversations WHERE id = ?", (cid,)).fetchone()
        return dict(row) if row else None

    def list(self, limit=100):
        with self._lock:
            rows = self._db.execute(
                "SELECT id, client, lead, tier, escalated, status, last_turn_status, updated_at "
                "FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def save_convo(self, cid, convo, last_turn_status=None, status=None):
        with self._lock:
            self._db.execute(
                "UPDATE conversations SET slots=?, history=?, tier=?, escalated=?, "
                "last_turn_status=COALESCE(?, last_turn_status), status=COALESCE(?, status), updated_at=? "
                "WHERE id=?",
                (json.dumps(convo.slots), json.dumps(convo.history), convo.tier,
                 1 if convo.escalated else 0, last_turn_status, status, time.time(), cid))
            self._db.commit()

    def log_turn(self, cid, role, text, status=None):
        with self._lock:
            self._db.execute(
                "INSERT INTO turns (convo_id, role, text, status, ts) VALUES (?,?,?,?,?)",
                (cid, role, text, status, time.time()))
            self._db.commit()

    def turns(self, cid):
        with self._lock:
            rows = self._db.execute(
                "SELECT role, text, status, ts FROM turns WHERE convo_id = ? ORDER BY seq", (cid,)).fetchall()
        return [dict(r) for r in rows]
