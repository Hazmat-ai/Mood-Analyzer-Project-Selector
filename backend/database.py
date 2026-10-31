import sqlite3
from pathlib import Path
from flask import g, current_app

SCHEMA = '''
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, csrf TEXT NOT NULL, expires INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_expiry ON sessions(expires);
CREATE TABLE IF NOT EXISTS picks (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 project_id TEXT NOT NULL, project_title TEXT NOT NULL, specialty TEXT NOT NULL,
 difficulty TEXT NOT NULL, timestamp INTEGER NOT NULL, completed INTEGER NOT NULL DEFAULT 0,
 request_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 UNIQUE(session_id, request_key)
);
CREATE INDEX IF NOT EXISTS picks_owner ON picks(session_id, timestamp DESC);
CREATE TABLE IF NOT EXISTS rate_limits (
 ip_hash TEXT PRIMARY KEY, reset_at INTEGER NOT NULL, requests INTEGER NOT NULL, creations INTEGER NOT NULL
);
PRAGMA user_version=1;
'''

def connect(path):
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=5000')
    return db

def initialize(path):
    Path(path).resolve().parent.mkdir(parents=True, exist_ok=True)
    db = connect(path)
    try:
        if db.execute('PRAGMA user_version').fetchone()[0] > 1:
            raise RuntimeError('Database schema is newer than this application')
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript(SCHEMA)
    finally:
        db.close()

def get_db():
    if 'db' not in g:
        g.db = connect(current_app.config['DATABASE'])
    return g.db

def close_db(error=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
