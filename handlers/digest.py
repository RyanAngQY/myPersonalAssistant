from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import local, owner_only
from models import from_iso


def agenda(repo, start, end, tz) -> str:
    items = [(from_iso(x["start_at"]), "📅", x["name"]) for x in repo.events_between(start, end)]
    items += [(from_iso(x["due_at"]), "☑️", x["name"]) for x in repo.tasks_due_between(start, end)]
    items.sort(key=lambda x: x[0])
    return "Nothing scheduled." if not items else "\n".join(f"{kind} {local(when, tz)} — {name}" for when, kind, name in items)


@owner_only
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tz = context.bot_data["settings"].timezone; start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    await update.effective_message.reply_text("Today:\n" + agenda(context.bot_data["repo"], start, start + timedelta(days=1), tz))


@owner_only
async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tz = context.bot_data["settings"].timezone; now = datetime.now(tz); start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    await update.effective_message.reply_text("This week:\n" + agenda(context.bot_data["repo"], start, start + timedelta(days=7), tz))
