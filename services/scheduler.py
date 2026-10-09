from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from models import PlannerRepository, from_iso


class PlannerScheduler:
    def __init__(self, repository: PlannerRepository, owner_id: int, bot, tz):
        self.repository, self.owner_id, self.bot, self.tz = repository, owner_id, bot, tz
        self.scheduler = AsyncIOScheduler(timezone=tz)

    def start(self) -> None:
        self.scheduler.add_job(self.deliver_reminders, "interval", minutes=1, id="reminders")
        self.scheduler.add_job(self.send_morning_digest, "cron", hour=8, minute=0, id="morning")
        self.scheduler.add_job(self.send_weekly_review, "cron", day_of_week="sun", hour=19, minute=0, id="review")
        self.scheduler.start()

    def add_task_reminders(self, task_id: int, due_at: datetime | None, importance: int) -> None:
        if not due_at: return
        self.repository.schedule_reminder("task", task_id, due_at)
        if importance == 3 and due_at - timedelta(days=1) > datetime.now(timezone.utc):
            self.repository.schedule_reminder("task", task_id, due_at - timedelta(days=1))

    def add_event_reminder(self, event_id: int, start_at: datetime) -> None:
        self.repository.schedule_reminder("event", event_id, start_at)

    async def deliver_reminders(self) -> None:
        now = datetime.now(timezone.utc)
        for reminder in self.repository.pending_reminders(now):
            item = self.repository.get_task(reminder["item_id"]) if reminder["item_type"] == "task" else self.repository.get_event(reminder["item_id"])
            if item and (reminder["item_type"] != "task" or item["status"] == "open"):
                when = from_iso(item["due_at"] if reminder["item_type"] == "task" else item["start_at"]).astimezone(self.tz)
                await self.bot.send_message(self.owner_id, f"⏰ Reminder: {item['name']} — {when:%a %d %b %H:%M}")
            self.repository.mark_reminder_sent(reminder["id"])

    async def send_morning_digest(self) -> None:
        today = datetime.now(self.tz).replace(hour=0, minute=0, second=0, microsecond=0)
        items = self.repository.events_between(today, today + timedelta(days=1)) + self.repository.tasks_due_between(today, today + timedelta(days=1))
        text = "☀️ Good morning. Nothing scheduled today." if not items else "☀️ Today:\n" + "\n".join(f"• {x['name']}" for x in items)
        await self.bot.send_message(self.owner_id, text)

    async def send_weekly_review(self) -> None:
        await self.bot.send_message(self.owner_id, "🗓 Weekly review: check /goals and /tasks, then plan your top 3 for the week.")
