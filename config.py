from dataclasses import dataclass
from pathlib import Path
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    token: str
    owner_id: int
    timezone: ZoneInfo
    database_path: Path


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    owner = os.getenv("OWNER_ID", "")
    if not token or not owner:
        raise RuntimeError("Set BOT_TOKEN and OWNER_ID in .env (see .env.example).")
    try:
        owner_id = int(owner)
    except ValueError as exc:
        raise RuntimeError("OWNER_ID must be a numeric Telegram user id.") from exc
    return Settings(
        token=token,
        owner_id=owner_id,
        timezone=ZoneInfo(os.getenv("TIMEZONE", "Asia/Singapore")),
        database_path=Path(os.getenv("DATABASE_PATH", "planner.sqlite3")),
    )
