"""Small app-owned event store. No client or model chooses a disk path."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from app.api.schemas import EventType, FileId

DEFAULT_DATABASE = Path(__file__).resolve().parents[2] / 'data' / 'ghost.sqlite3'


class Repository:
    def __init__(self, database: Path = DEFAULT_DATABASE):
        self.database = database  # Injection is for tests, never an HTTP field.

    @contextmanager
    def transaction(self):
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=2)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA foreign_keys = ON')
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise sqlite3.DatabaseError('Unsupported save version')
            db.execute('''CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, run_index INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK(status IN ('active','completed','abandoned')),
                started_at TEXT NOT NULL, ended_at TEXT,
                parent_run_id TEXT REFERENCES runs(id))''')
            db.execute('''CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(id), type TEXT NOT NULL,
                target_id TEXT, payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL)''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id, id)')
            db.execute('PRAGMA user_version = 1')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def create_run(db):
        run_id = str(uuid4())
        index = db.execute('SELECT COALESCE(MAX(run_index), 0) + 1 FROM runs').fetchone()[0]
        db.execute('INSERT INTO runs(id, run_index, status, started_at) VALUES (?, ?, ?, ?)',
                   (run_id, index, 'active', datetime.now(timezone.utc).isoformat()))
        Repository.append(db, run_id, 'run_started')
        return run_id

    @staticmethod
    def get_run(db, run_id: str):
        return db.execute('SELECT * FROM runs WHERE id = ?', (run_id,)).fetchone()

    @staticmethod
    def events(db, run_id: str):
        return db.execute('SELECT * FROM events WHERE run_id = ? ORDER BY id', (run_id,)).fetchall()

    @staticmethod
    def append(db, run_id: str, event: EventType, target: FileId | None = None, payload=None):
        db.execute('INSERT INTO events(run_id,type,target_id,payload_json,created_at) VALUES (?,?,?,?,?)',
                   (run_id, event, target, json.dumps(payload or {}), datetime.now(timezone.utc).isoformat()))
