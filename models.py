"""Small SQLite repository; all timestamps are ISO-8601 UTC strings."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Iterable


class PlannerRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.db = connection

    def add_task(self, name: str, due_at: datetime | None, importance: int, goal_id: int | None = None) -> int:
        cur = self.db.execute("INSERT INTO tasks(name,due_at,importance,goal_id) VALUES(?,?,?,?)",
                              (name, iso(due_at), importance, goal_id))
        self.db.commit()
        return cur.lastrowid

    def add_event(self, name: str, start_at: datetime, end_at: datetime | None = None, location: str | None = None) -> int:
        cur = self.db.execute("INSERT INTO events(name,start_at,end_at,location) VALUES(?,?,?,?)",
                              (name, iso(start_at), iso(end_at), location))
        self.db.commit()
        return cur.lastrowid

    def add_goal(self, name: str, target_date: datetime | None, target_value: float | None = None, description: str | None = None) -> int:
        cur = self.db.execute("INSERT INTO goals(name,target_date,target_value,description) VALUES(?,?,?,?)",
                              (name, iso(target_date), target_value, description))
        self.db.commit()
        return cur.lastrowid

    def get_task(self, task_id: int): return self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    def get_event(self, event_id: int): return self.db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()

    def open_tasks(self, start: datetime | None = None, end: datetime | None = None) -> list:
        sql = "SELECT * FROM tasks WHERE status='open'"
        args: list = []
        if start: sql += " AND (due_at IS NULL OR due_at >= ?)"; args.append(iso(start))
        if end: sql += " AND (due_at IS NULL OR due_at < ?)"; args.append(iso(end))
        sql += " ORDER BY due_at IS NULL, due_at, importance DESC, id"
        return self.db.execute(sql, args).fetchall()

    def events_between(self, start: datetime, end: datetime) -> list:
        return self.db.execute("SELECT * FROM events WHERE start_at>=? AND start_at<? ORDER BY start_at", (iso(start), iso(end))).fetchall()

    def tasks_due_between(self, start: datetime, end: datetime) -> list:
        return self.db.execute("SELECT * FROM tasks WHERE status='open' AND due_at>=? AND due_at<? ORDER BY due_at, importance DESC", (iso(start), iso(end))).fetchall()

    def complete_task(self, task_id: int, now: datetime) -> bool:
        cur = self.db.execute("UPDATE tasks SET status='done',completed_at=? WHERE id=? AND status='open'", (iso(now), task_id))
        self.db.commit(); return cur.rowcount == 1

    def undo_task(self, task_id: int) -> None:
        self.db.execute("DELETE FROM tasks WHERE id=?", (task_id,)); self.db.commit()
    def undo_event(self, event_id: int) -> None:
        self.db.execute("DELETE FROM events WHERE id=?", (event_id,)); self.db.commit()

    def snooze_task(self, task_id: int, due_at: datetime) -> bool:
        cur = self.db.execute("UPDATE tasks SET due_at=? WHERE id=? AND status='open'", (iso(due_at), task_id))
        self.db.commit(); return cur.rowcount == 1

    def goals(self) -> list:
        return self.db.execute("SELECT g.*, (SELECT count(*) FROM tasks t WHERE t.goal_id=g.id) total, (SELECT count(*) FROM tasks t WHERE t.goal_id=g.id AND t.status='done') done FROM goals g WHERE status='active' ORDER BY target_date IS NULL, target_date").fetchall()

    def update_goal_progress(self, goal_id: int, value: float) -> bool:
        cur = self.db.execute("UPDATE goals SET current_value=? WHERE id=? AND status='active'", (value, goal_id)); self.db.commit(); return cur.rowcount == 1

    def schedule_reminder(self, item_type: str, item_id: int, when: datetime) -> None:
        self.db.execute("INSERT OR IGNORE INTO reminders(item_type,item_id,remind_at) VALUES(?,?,?)", (item_type, item_id, iso(when))); self.db.commit()

    def pending_reminders(self, now: datetime) -> list:
        return self.db.execute("SELECT * FROM reminders WHERE sent=0 AND remind_at<=? ORDER BY remind_at", (iso(now),)).fetchall()

    def mark_reminder_sent(self, reminder_id: int) -> None:
        self.db.execute("UPDATE reminders SET sent=1 WHERE id=?", (reminder_id,)); self.db.commit()

    def overlaps(self, start: datetime, end: datetime | None = None) -> list:
        end = end or start + timedelta(minutes=1)
        return self.db.execute("SELECT * FROM events WHERE start_at < ? AND COALESCE(end_at, start_at) > ?", (iso(end), iso(start))).fetchall()


def iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat() if value else None


def from_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
