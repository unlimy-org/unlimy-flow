from __future__ import annotations

from datetime import date, timedelta

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def moderation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Опубликовать сейчас", callback_data="publish_now")
    builder.button(text="🔁 Перегенерировать", callback_data="regenerate_post")
    builder.button(text="🕒 Запланировать", callback_data="schedule_open")
    builder.button(text="❌ Отмена", callback_data="cancel_post")
    builder.adjust(2, 2)
    return builder.as_markup()


def schedule_intervals_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="+15 мин", callback_data="sched_in:15")
    builder.button(text="+30 мин", callback_data="sched_in:30")
    builder.button(text="+1 час", callback_data="sched_in:60")
    builder.button(text="+2 часа", callback_data="sched_in:120")
    builder.button(text="Выбрать день", callback_data="sched_pick_day")
    builder.button(text="⬅️ Назад", callback_data="sched_back")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def schedule_days_keyboard(days: int = 7) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i in range(days):
        d = date.today() + timedelta(days=i)
        label = "Сегодня" if i == 0 else ("Завтра" if i == 1 else d.strftime("%d.%m"))
        builder.button(text=label, callback_data=f"sched_day:{d.strftime('%Y%m%d')}")
    builder.button(text="⬅️ Назад", callback_data="schedule_open")
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup()


def schedule_times_keyboard(day_yyyymmdd: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    slots = ["09:00", "12:00", "15:00", "18:00", "21:00", "23:00"]
    for slot in slots:
        hhmm = slot.replace(":", "")
        builder.button(text=slot, callback_data=f"sched_set:{day_yyyymmdd}:{hhmm}")
    builder.button(text="⬅️ К дням", callback_data="sched_pick_day")
    builder.adjust(3, 3, 1)
    return builder.as_markup()

