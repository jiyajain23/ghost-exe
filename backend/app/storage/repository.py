"""Small app-owned event store. No client or model chooses a disk path."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from uuid import uuid4

from app.api.schemas import EventType, FileId, RunStatus

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
                id TEXT PRIMARY KEY,
                run_index INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK(status IN ('active','completed','abandoned')),
                started_at TEXT NOT NULL,
                ended_at TEXT,
                parent_run_id TEXT REFERENCES runs(id)
            )''')

            db.execute('''CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES runs(id),
                type TEXT NOT NULL,
                target_id TEXT,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            )''')
            db.execute('CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id, id)')

            db.execute('''CREATE TABLE IF NOT EXISTS ghost_beliefs (
                run_id TEXT NOT NULL REFERENCES runs(id),
                belief_key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                PRIMARY KEY (run_id, belief_key)
            )''')

            db.execute('''CREATE TABLE IF NOT EXISTS secrets (
                key TEXT PRIMARY KEY,
                source_file_id TEXT NOT NULL,
                minimum_clue TEXT NOT NULL
            )''')

            db.execute('''INSERT OR IGNORE INTO secrets(key, source_file_id, minimum_clue) VALUES
                ('door_relay_access', 'F04', 'C1_ACCESS_CONTRADICTION'),
                ('manual_lock_tamper', 'F06', 'C2_LOG_TAMPERING'),
                ('helper_lock_event', 'F08', 'C3_LOCK_PROOF'),
                ('relay_isolation_procedure', 'F10', 'C4_CONTAINMENT_READY')
            ''')

            db.execute('PRAGMA user_version = 1')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def create_run(db, parent_run_id: str | None = None):
        run_id = str(uuid4())
        index = db.execute('SELECT COALESCE(MAX(run_index), 0) + 1 FROM runs').fetchone()[0]
        db.execute(
            'INSERT INTO runs(id, run_index, status, started_at, parent_run_id) VALUES (?, ?, ?, ?, ?)',
            (run_id, index, 'active', datetime.now(timezone.utc).isoformat(), parent_run_id),
        )
        Repository.append(db, run_id, 'run_started')
        return run_id

    @staticmethod
    def get_run(db, run_id: str):
        return db.execute('SELECT * FROM runs WHERE id = ?', (run_id,)).fetchone()

    @staticmethod
    def update_run_status(db, run_id: str, status: RunStatus, ended_at: str | None = None):
        ended = ended_at or datetime.now(timezone.utc).isoformat()
        db.execute('UPDATE runs SET status = ?, ended_at = ? WHERE id = ?', (status, ended, run_id))

    @staticmethod
    def events(db, run_id: str):
        return db.execute('SELECT * FROM events WHERE run_id = ? ORDER BY id', (run_id,)).fetchall()

    @staticmethod
    def append(db, run_id: str, event: EventType, target: FileId | str | None = None, payload=None):
        db.execute(
            'INSERT INTO events(run_id, type, target_id, payload_json, created_at) VALUES (?, ?, ?, ?, ?)',
            (run_id, event, target, json.dumps(payload or {}), datetime.now(timezone.utc).isoformat()),
        )

    @staticmethod
    def set_belief(db, run_id: str, belief_key: str, value):
        db.execute(
            'INSERT OR REPLACE INTO ghost_beliefs(run_id, belief_key, value_json) VALUES (?, ?, ?)',
            (run_id, belief_key, json.dumps(value)),
        )

    @staticmethod
    def get_beliefs(db, run_id: str) -> dict:
        rows = db.execute('SELECT belief_key, value_json FROM ghost_beliefs WHERE run_id = ?', (run_id,)).fetchall()
        return {r['belief_key']: json.loads(r['value_json']) for r in rows}

    @staticmethod
    def has_qualified_prior_run(db, current_run_id: str) -> bool:
        prior_run = db.execute(
            '''SELECT 1 FROM events
               WHERE run_id != ? AND type IN ('photo_choice', 'file_opened', 'chat_category')
               LIMIT 1''',
            (current_run_id,),
        ).fetchone()
        return prior_run is not None

    @staticmethod
    def clear_history(db):
        db.execute('DELETE FROM events')
        db.execute('DELETE FROM ghost_beliefs')
        db.execute('UPDATE runs SET parent_run_id = NULL')
        db.execute('DELETE FROM runs')
