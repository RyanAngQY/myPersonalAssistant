from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from handlers.common import local, owner_only
from models import from_iso
from services.calendar_img import render_month
from services.parsing import parse_when


@owner_only
async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    parts = [p.strip() for p in update.effective_message.text.partition(" ")[2].split("|")]
    if len(parts) < 2: await update.effective_message.reply_text("Usage: /addevent Dentist | 15 Oct 3pm [| location]"); return
    start = parse_when(parts[1], context.bot_data["settings"].timezone)
    if not parts[0] or not start: await update.effective_message.reply_text("I could not read that date. Please try a specific date and time."); return
    repo = context.bot_data["repo"]; conflicts = repo.overlaps(start)
    event_id = repo.add_event(parts[0], start, location=parts[2] if len(parts) > 2 else None)
    context.bot_data["scheduler"].add_event_reminder(event_id, start)
    warning = "\n⚠️ It overlaps an existing event." if conflicts else ""
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Undo", callback_data=f"undo:event:{event_id}")]])
    await update.effective_message.reply_text(f"Added event #{event_id}: {parts[0]} — {local(start, context.bot_data['settings'].timezone)}{warning}", reply_markup=keyboard)


@owner_only
async def calendar_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now(context.bot_data["settings"].timezone)
    await send_calendar(update.effective_message, context, now.year, now.month)


async def send_calendar(message, context, year: int, month: int) -> None:
    tz = context.bot_data["settings"].timezone; repo = context.bot_data["repo"]
    start = datetime(year, month, 1, tzinfo=tz); end = (start + timedelta(days=32)).replace(day=1)
    image = render_month(year, month, repo.events_between(start, end), repo.tasks_due_between(start, end), tz)
    previous = (start - timedelta(days=1)).replace(day=1); following = end
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("◀", callback_data=f"calendar:{previous.year}:{previous.month}"), InlineKeyboardButton("▶", callback_data=f"calendar:{following.year}:{following.month}")]])
    await message.reply_photo(image, caption="🔵 events   🔴 task due", reply_markup=keyboard)
