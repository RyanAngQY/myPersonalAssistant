# Telegram Planner Bot

A private, free-to-run Telegram planner using Python, SQLite, APScheduler, and long polling. All stored timestamps are UTC; input and display default to `Asia/Singapore`.

## Set up

1. Create a Telegram bot with [@BotFather](https://t.me/BotFather) and get your numeric user ID (for example, message [@userinfobot](https://t.me/userinfobot)).
2. Install Python 3.11+, then create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`, then fill `BOT_TOKEN` and `OWNER_ID`.
5. Start it with `python bot.py`. It uses long polling, so no domain or HTTPS setup is needed.

## Commands

| Command | Example |
| --- | --- |
| Add task | `/addtask Submit report | fri 5pm | high` |
| Link task to goal | `/addtask Run intervals | tomorrow 7am | medium | 1` |
| List/complete | `/tasks`, `/done 3` |
| Add event | `/addevent Dentist | 15 Oct 3pm | Orchard Road` |
| Agenda/calendar | `/today`, `/week`, `/calendar` |
| Add goal | `/addgoal Run 5K | Dec 31 | 5` |
| Goal updates | `/goals`, `/progress 1 2.5` |

Tasks include Done and Snooze controls. Tasks and events get a reminder at their scheduled time; high-priority tasks also get a 24-hour heads-up. The 08:00 digest and Sunday 19:00 review run in the configured timezone. Because reminder state is in SQLite, bot restarts are safe.

For an always-on deployment, copy the project and its SQLite database to an Oracle Always Free VM (or a home server) and run it under a restart-on-failure service manager. Never commit `.env` or the SQLite database.
