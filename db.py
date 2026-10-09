import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, start_at TEXT NOT NULL, end_at TEXT,
 location TEXT, notes TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS goals (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, description TEXT, target_date TEXT,
 target_value REAL, current_value REAL NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'active',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tasks (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, due_at TEXT, importance INTEGER NOT NULL DEFAULT 2
 CHECK(importance BETWEEN 1 AND 3), status TEXT NOT NULL DEFAULT 'open', goal_id INTEGER,
 recurrence TEXT, completed_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(goal_id) REFERENCES goals(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS reminders (
 id INTEGER PRIMARY KEY, item_type TEXT NOT NULL CHECK(item_type IN ('task','event')),
 item_id INTEGER NOT NULL, remind_at TEXT NOT NULL, sent INTEGER NOT NULL DEFAULT 0,
 UNIQUE(item_type, item_id, remind_at)
);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(status, due_at);
CREATE INDEX IF NOT EXISTS idx_events_start ON events(start_at);
CREATE INDEX IF NOT EXISTS idx_reminders_pending ON reminders(sent, remind_at);
"""


def connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    connection.commit()
    return connection
