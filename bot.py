"""Telegram entry point. Uses long polling; no public web server is needed."""
import logging

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from config import load_settings
from db import connect
from handlers.digest import today, week
from handlers.events import add_event, calendar_view, send_calendar
from handlers.goals import add_goal, goals, progress
from handlers.tasks import add_task, done, task_callback, tasks
from models import PlannerRepository
from services.scheduler import PlannerScheduler

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = context.bot_data["settings"]
    if update.effective_user.id != settings.owner_id:
        await update.effective_message.reply_text("This is a private planner bot."); return
    await update.effective_message.reply_text(
        "Planner ready.\n\n"
        "/addtask Name | fri 5pm | high [| goal id]\n"
        "/addevent Name | 15 Oct 3pm [| location]\n"
        "/tasks, /done ID, /today, /week, /calendar\n"
        "/addgoal Name | Dec 31 [| numeric target]\n"
        "/goals, /progress GOAL_ID VALUE"
    )


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    settings = context.bot_data["settings"]
    if query.from_user.id != settings.owner_id:
        await query.answer("Private bot", show_alert=True); return
    await query.answer()
    bits = query.data.split(":")
    if bits[0] == "done": await task_callback(query, context, "done", int(bits[1]))
    elif bits[0] == "snooze": await task_callback(query, context, "snooze", int(bits[1]), bits[2])
    elif bits[0] == "undo":
        repo = context.bot_data["repo"]
        (repo.undo_task if bits[1] == "task" else repo.undo_event)(int(bits[2]))
        await query.edit_message_text("Undone.")
    elif bits[0] == "calendar":
        await send_calendar(query.message, context, int(bits[1]), int(bits[2]))


def main() -> None:
    settings = load_settings()
    repo = PlannerRepository(connect(settings.database_path))
    application = Application.builder().token(settings.token).build()
    scheduler = PlannerScheduler(repo, settings.owner_id, application.bot, settings.timezone)
    application.bot_data.update(settings=settings, repo=repo, scheduler=scheduler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("addtask", add_task))
    application.add_handler(CommandHandler("tasks", tasks))
    application.add_handler(CommandHandler("done", done))
    application.add_handler(CommandHandler("addevent", add_event))
    application.add_handler(CommandHandler("calendar", calendar_view))
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("addgoal", add_goal))
    application.add_handler(CommandHandler("goals", goals))
    application.add_handler(CommandHandler("progress", progress))
    application.add_handler(CallbackQueryHandler(callback))
    scheduler.start()
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
