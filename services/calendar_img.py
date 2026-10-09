from __future__ import annotations

import calendar
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from models import from_iso


def render_month(year: int, month: int, events: list, tasks: list, timezone: ZoneInfo) -> BytesIO:
    width, height, header, cell_h = 980, 720, 110, 100
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    # Arial is present on typical Windows hosts; fall back for minimal Linux VMs.
    try:
        title = ImageFont.truetype("arial.ttf", 30)
        regular = ImageFont.truetype("arial.ttf", 18)
        small = ImageFont.truetype("arial.ttf", 14)
    except OSError:
        title = regular = small = ImageFont.load_default()
    draw.rectangle((0, 0, width, header), fill="#1d4ed8")
    draw.text((30, 25), f"{calendar.month_name[month]} {year}", font=title, fill="white")
    for index, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
        draw.text((20 + index * 135, 78), day, font=regular, fill="#dbeafe")
    event_days = {from_iso(row["start_at"]).astimezone(timezone).day for row in events}
    task_days = {from_iso(row["due_at"]).astimezone(timezone).day for row in tasks if row["due_at"]}
    for row, week in enumerate(calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)):
        for col, day in enumerate(week):
            x, y = 10 + col * 138, header + row * cell_h
            draw.rounded_rectangle((x, y, x + 128, y + 90), 8, fill="#ffffff", outline="#cbd5e1")
            if day:
                draw.text((x + 10, y + 8), str(day), font=regular, fill="#0f172a")
                if day in event_days:
                    draw.ellipse((x + 10, y + 42, x + 25, y + 57), fill="#2563eb")
                    draw.text((x + 30, y + 39), "event", font=small, fill="#1e3a8a")
                if day in task_days:
                    draw.ellipse((x + 10, y + 64, x + 25, y + 79), fill="#dc2626")
                    draw.text((x + 30, y + 61), "task due", font=small, fill="#7f1d1d")
    stream = BytesIO(); stream.name = f"calendar-{year}-{month:02}.png"
    image.save(stream, "PNG"); stream.seek(0)
    return stream
