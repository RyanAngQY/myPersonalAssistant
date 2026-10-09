from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from handlers.common import owner_only
from models import from_iso
from services.parsing import parse_when


@owner_only
async def add_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.text.partition(" ")[2]
    parts = [x.strip() for x in text.split("|")]
    if not parts or not parts[0]: await update.effective_message.reply_text("Usage: /addgoal Run 5K | Dec 31 [| numeric target]"); return
    date = parse_when(parts[1], context.bot_data["settings"].timezone) if len(parts) > 1 and parts[1] else None
    target = float(parts[2]) if len(parts) > 2 and parts[2].replace(".", "", 1).isdigit() else None
    goal_id = context.bot_data["repo"].add_goal(parts[0], date, target)
    await update.effective_message.reply_text(f"Added goal #{goal_id}: {parts[0]}. Link tasks with /addtask ... | ... | ... | {goal_id}")


@owner_only
async def goals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = context.bot_data["repo"].goals(); tz = context.bot_data["settings"].timezone
    if not rows: await update.effective_message.reply_text("No active goals yet. Use /addgoal."); return
    lines = []
    for goal in rows:
        percent = min(100, round((goal["current_value"] / goal["target_value"] * 100) if goal["target_value"] else (goal["done"] / goal["total"] * 100 if goal["total"] else 0)))
        bar = "▓" * (percent // 10) + "░" * (10 - percent // 10)
        deadline = from_iso(goal["target_date"])
        remaining = f", {(deadline.astimezone(tz).date() - datetime.now(tz).date()).days} days left" if deadline else ""
        lines.append(f"#{goal['id']} {goal['name']}\n{bar} {percent}%{remaining}")
    await update.effective_message.reply_text("\n\n".join(lines))


@owner_only
async def progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 2 or not context.args[0].isdigit(): await update.effective_message.reply_text("Usage: /progress GOAL_ID VALUE"); return
    try: value = float(context.args[1])
    except ValueError: await update.effective_message.reply_text("VALUE must be a number."); return
    ok = context.bot_data["repo"].update_goal_progress(int(context.args[0]), value)
    await update.effective_message.reply_text("Progress updated. ✅" if ok else "Active goal not found.")
