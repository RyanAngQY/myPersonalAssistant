from functools import wraps

from telegram import Update


def owner_only(callback):
    @wraps(callback)
    async def wrapped(update: Update, context):
        if not update.effective_user or update.effective_user.id != context.bot_data["settings"].owner_id:
            if update.effective_message:
                await update.effective_message.reply_text("This is a private planner bot.")
            return
        return await callback(update, context)
    return wrapped


def local(dt, tz):
    return dt.astimezone(tz).strftime("%a %d %b %H:%M") if dt else "no due date"
