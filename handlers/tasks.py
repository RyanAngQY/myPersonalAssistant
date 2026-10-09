from datetime import timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.common import local, owner_only
from models import from_iso
from services.parsing import parse_importance, parse_when


@owner_only
async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/addtask Name | due phrase | high [| goal id]"""
    parts = update.effective_message.text.partition(" ")[2].split("|")
    if len(parts) < 3:
        await update.effective_message.reply_text("Usage: /addtask Submit report | fri 5pm | high [| goal id]"); return
    name, due_text, priority = (x.strip() for x in parts[:3])
    due_at, importance = parse_when(due_text, context.bot_data["settings"].timezone), parse_importance(priority)
    if not name or not due_at or not importance:
        await update.effective_message.reply_text("I could not read that. Use a name, a clear date, and high/medium/low."); return
    goal_id = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else None
    repo = context.bot_data["repo"]; task_id = repo.add_task(name, due_at, importance, goal_id)
    context.bot_data["scheduler"].add_task_reminders(task_id, due_at, importance)
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Undo", callback_data=f"undo:task:{task_id}")]])
    await update.effective_message.reply_text(f"Added task #{task_id}: {name} — {local(due_at, context.bot_data['settings'].timezone)}", reply_markup=keyboard)


@owner_only
async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = context.bot_data["repo"].open_tasks()
    if not rows: await update.effective_message.reply_text("No open tasks. 🎉"); return
    tz = context.bot_data["settings"].timezone
    for row in rows:
        due = local(from_iso(row["due_at"]), tz) if row["due_at"] else "no due date"
        icon = "🔴" if row["importance"] == 3 else "🟡" if row["importance"] == 2 else "🟢"
        keys = [[InlineKeyboardButton("✅ Done", callback_data=f"done:{row['id']}"), InlineKeyboardButton("⏰ +1h", callback_data=f"snooze:{row['id']}:hour")], [InlineKeyboardButton("Tomorrow", callback_data=f"snooze:{row['id']}:tomorrow")]]
        await update.effective_message.reply_text(f"#{row['id']} {icon} {row['name']}\nDue: {due}", reply_markup=InlineKeyboardMarkup(keys))


@owner_only
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg = context.args[0] if context.args else ""
    if not arg.isdigit(): await update.effective_message.reply_text("Usage: /done TASK_ID"); return
    ok = context.bot_data["repo"].complete_task(int(arg), update.effective_message.date)
    await update.effective_message.reply_text("Marked done. ✅" if ok else "That open task was not found.")


async def task_callback(query, context, action: str, task_id: int, extra: str | None = None) -> None:
    repo = context.bot_data["repo"]
    if action == "done":
        repo.complete_task(task_id, query.message.date); await query.edit_message_text("Marked done. ✅")
    elif action == "snooze":
        base = from_iso(repo.get_task(task_id)["due_at"]) or query.message.date
        new_due = base + (timedelta(hours=1) if extra == "hour" else timedelta(days=1))
        repo.snooze_task(task_id, new_due); await query.edit_message_text(f"Snoozed until {local(new_due, context.bot_data['settings'].timezone)}.")
