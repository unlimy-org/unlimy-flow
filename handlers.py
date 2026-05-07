from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from cleaner import clean_forwarded_text
from config import Config
from db import Database
from formatter import format_for_telegram_html
from keyboards import (
    moderation_keyboard,
    schedule_days_keyboard,
    schedule_intervals_keyboard,
    schedule_times_keyboard,
)
from llm import LLMClient
from redis_client import RedisClient

router = Router()
logger = logging.getLogger(__name__)

CAPTION_LIMIT = 1024
try:
    TZ = ZoneInfo("Europe/Moscow")
except ZoneInfoNotFoundError:
    TZ = timezone(timedelta(hours=3))


def _build_metadata(news_text: str) -> dict[str, Any]:
    lower = news_text.lower()
    tech_markers = ["dpi", "белые списки", "блокировк", "протокол", "отключение интернета", "сбой"]
    geo_markers = ["росси", "рф", "снг", "регион"]
    is_tech = any(m in lower for m in tech_markers) and any(g in lower for g in geo_markers)
    return {"is_technical_blocking_in_russia": is_tech}


def _extract_media(message: Message) -> tuple[str | None, str | None]:
    if message.photo:
        return "photo", message.photo[-1].file_id
    if message.video:
        return "video", message.video.file_id
    return None, None


async def _extract_news_text(message: Message) -> str:
    text = message.text or message.caption or ""
    if message.forward_origin:
        return clean_forwarded_text(text)
    return text.strip()


def _safe_caption(formatted_text: str) -> str:
    if len(formatted_text) <= CAPTION_LIMIT:
        return formatted_text
    clipped = formatted_text[:1000].rstrip()
    return clipped if clipped.endswith("...") else clipped + "..."


async def _publish_to_channel(
    message_or_callback: Message | CallbackQuery,
    channel_id: str,
    post_text: str,
    media_type: str | None,
    media_file_id: str | None,
) -> int:
    bot = message_or_callback.bot if isinstance(message_or_callback, Message) else message_or_callback.message.bot
    formatted = format_for_telegram_html(post_text)
    if media_type == "photo" and media_file_id:
        sent = await bot.send_photo(chat_id=channel_id, photo=media_file_id, caption=_safe_caption(formatted))
        return sent.message_id
    if media_type == "video" and media_file_id:
        sent = await bot.send_video(chat_id=channel_id, video=media_file_id, caption=_safe_caption(formatted))
        return sent.message_id
    sent = await bot.send_message(chat_id=channel_id, text=formatted)
    return sent.message_id


async def _timeout_pending_post(
    user_id: int,
    bot_message_id: int,
    chat_id: int,
    redis_client: RedisClient,
    bot,
) -> None:
    await asyncio.sleep(1800)
    payload = await redis_client.get_pending_post(user_id)
    if not payload or payload.get("preview_message_id") != bot_message_id:
        return
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=bot_message_id,
            text="⏰ Таймаут. Пост не опубликован.",
            reply_markup=None,
        )
    finally:
        await redis_client.delete_pending_post(user_id)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Привет! Я unlimyFlow.\n\n"
        "Отправьте текст новости или перешлите пост из канала, и я подготовлю публикацию.\n\n"
        "Команды: /mode /status /history /help"
    )
@router.message(Command("emoji_id"))
async def cmd_emoji_id(message: Message) -> None:
    entities = message.entities or []
    for e in entities:
        if e.type == "custom_emoji":
            await message.answer(f"CUSTOM_STAR_EMOJI_ID={e.custom_emoji_id}")
            return
    await message.answer("В этом сообщении нет custom emoji. Отправьте /emoji_id вместе с кастомной ⭐️")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "/start — приветствие\n"
        "/mode — переключить режим instant/queue\n"
        "/status — текущий режим и статистика\n"
        "/history — последние 5 постов\n"
        "/scheduled — запланированные публикации\n"
        "/help — список команд"
    )


@router.message(Command("mode"))
async def cmd_mode(message: Message, redis_client: RedisClient, config: Config) -> None:
    current = await redis_client.get_publish_mode(config.publish_mode)
    new_mode = "instant" if current == "queue" else "queue"
    await redis_client.set_publish_mode(new_mode)
    await message.answer(f"Режим публикации переключен: {new_mode}")


@router.message(Command("status"))
async def cmd_status(message: Message, db: Database, redis_client: RedisClient, config: Config) -> None:
    mode = await redis_client.get_publish_mode(config.publish_mode)
    total = await db.count_total()
    last_24h = await db.count_last_24h()
    session = await redis_client.get_session_counter()
    await message.answer(
        f"Текущий режим: {mode}\n"
        f"Всего сгенерировано: {total}\n"
        f"За 24 часа: {last_24h}\n"
        f"За сессию: {session}"
    )


@router.message(Command("history"))
async def cmd_history(message: Message, db: Database) -> None:
    posts = await db.get_recent_posts(limit=5)
    if not posts:
        await message.answer("История пока пуста.")
        return
    lines = []
    for post in posts:
        dt = post.created_at.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"{dt} | #{post.id} | {post.post_text.replace(chr(10), ' ')[:100]}")
    await message.answer("\n".join(lines))


@router.message(Command("scheduled"))
async def cmd_scheduled(message: Message, db: Database) -> None:
    rows = await db.list_pending_scheduled(limit=10)
    if not rows:
        await message.answer("Запланированных публикаций нет.")
        return
    for row in rows:
        dt = row["publish_at"].astimezone(TZ).strftime("%d.%m %H:%M")
        preview = row["post_text"].replace("\n", " ")[:120]
        media = " +медиа" if row["media_type"] else ""
        text = f"ID {row['id']} | Пост #{row['post_id']} | {dt} (МСК){media}\n{preview}"
        kb = InlineKeyboardBuilder()
        kb.button(text="🗑 Отменить", callback_data=f"sched_cancel:{row['id']}")
        await message.answer(text, reply_markup=kb.as_markup())


@router.message(F.text | F.caption | F.photo | F.video)
async def news_input_handler(
    message: Message,
    db: Database,
    redis_client: RedisClient,
    llm: LLMClient,
    config: Config,
) -> None:
    news_text = await _extract_news_text(message)
    media_type, media_file_id = _extract_media(message)
    if not news_text:
        logger.warning("Received empty news text after cleaning")
        await message.answer("⚠️ После очистки текст пуст. Отправьте другую новость.")
        return

    metadata = _build_metadata(news_text)
    logger.info("News received: %s", news_text[:50].replace("\n", " "))
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    await message.answer("⚙️ Принято. unlimyFlow готовит пост...")

    target_max_chars = 1000 if media_type and media_file_id else 1800
    try:
        post_text, violations = await llm.process_news(news_text, metadata, max_len=target_max_chars, critic_passes=1)
        if violations:
            logger.warning("Post has unresolved violations: %s", violations)
    except Exception:
        logger.exception("Failed to generate post")
        await message.answer("❌ unlimyFlow: не удалось сгенерировать пост. Попробуйте позже.")
        return

    mode = await redis_client.get_publish_mode(config.publish_mode)
    post_id = await db.insert_post(news_text=news_text, post_text=post_text, publish_mode=mode)
    await redis_client.incr_session_counter()

    if mode == "instant":
        try:
            msg_id = await _publish_to_channel(message, config.channel_id, post_text, media_type, media_file_id)
        except TelegramBadRequest:
            logger.exception("Failed to publish instantly to channel_id=%s", config.channel_id)
            await message.answer("❌ Не удалось опубликовать в канал. Проверьте CHANNEL_ID и права бота.")
            return
        await db.mark_published(post_id)
        logger.info("Post published instantly, post_id=%s, message_id=%s", post_id, msg_id)
        await message.answer("✅ Опубликовано в канал.")
        return

    media_note = "\n\n📎 Медиа будет приложено к публикации." if media_type and media_file_id else ""
    preview = await message.answer(
        f"Предпросмотр поста:{media_note}\n\n{format_for_telegram_html(post_text)}",
        reply_markup=moderation_keyboard(),
    )
    payload: dict[str, Any] = {
        "post_id": post_id,
        "news_text": news_text,
        "metadata": metadata,
        "post_text": post_text,
        "preview_message_id": preview.message_id,
        "media_type": media_type,
        "media_file_id": media_file_id,
    }
    await redis_client.set_pending_post(message.from_user.id, payload, ttl_sec=1800)
    asyncio.create_task(
        _timeout_pending_post(
            user_id=message.from_user.id,
            bot_message_id=preview.message_id,
            chat_id=message.chat.id,
            redis_client=redis_client,
            bot=message.bot,
        )
    )


@router.callback_query(F.data == "publish_now")
async def cb_publish_now(callback: CallbackQuery, db: Database, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    try:
        msg_id = await _publish_to_channel(
            callback, config.channel_id, payload["post_text"], payload.get("media_type"), payload.get("media_file_id")
        )
    except TelegramBadRequest:
        logger.exception("Failed to publish queued post to channel_id=%s", config.channel_id)
        await callback.answer("Ошибка публикации: проверьте CHANNEL_ID и права бота.", show_alert=True)
        return
    await db.mark_published(int(payload["post_id"]))
    await redis_client.delete_pending_post(callback.from_user.id)
    await callback.message.edit_text("✅ Опубликовано", reply_markup=None)
    logger.info("Post published from moderation, post_id=%s, message_id=%s", payload["post_id"], msg_id)
    await callback.answer()


@router.callback_query(F.data == "regenerate_post")
async def cb_regenerate_post(
    callback: CallbackQuery,
    db: Database,
    redis_client: RedisClient,
    config: Config,
    llm: LLMClient,
) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    await callback.answer("Перегенерирую...")
    news_text = payload.get("news_text", "")
    metadata = payload.get("metadata", _build_metadata(news_text))
    target_max_chars = 1000 if payload.get("media_type") and payload.get("media_file_id") else 1800

    try:
        post_text, _ = await llm.process_news(news_text, metadata, max_len=target_max_chars, critic_passes=1)
    except Exception:
        logger.exception("Failed to regenerate post")
        await callback.message.answer("❌ Не удалось перегенерировать пост.")
        return

    new_post_id = await db.insert_post(news_text=news_text, post_text=post_text, publish_mode="queue")
    payload["post_text"] = post_text
    payload["post_id"] = new_post_id
    await redis_client.set_pending_post(callback.from_user.id, payload, ttl_sec=1800)

    media_note = "\n\n📎 Медиа будет приложено к публикации." if payload.get("media_type") and payload.get("media_file_id") else ""
    await callback.message.edit_text(
        f"Предпросмотр поста:{media_note}\n\n{format_for_telegram_html(post_text)}",
        reply_markup=moderation_keyboard(),
    )


@router.callback_query(F.data == "schedule_open")
async def cb_schedule_open(callback: CallbackQuery, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=schedule_intervals_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("sched_in:"))
async def cb_sched_in(callback: CallbackQuery, db: Database, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    minutes = int(callback.data.split(":")[1])
    publish_at = datetime.now(TZ) + timedelta(minutes=minutes)
    schedule_id = await db.schedule_post(
        post_id=int(payload["post_id"]),
        channel_id=config.channel_id,
        post_text=payload["post_text"],
        publish_at=publish_at,
        media_type=payload.get("media_type"),
        media_file_id=payload.get("media_file_id"),
    )
    await redis_client.delete_pending_post(callback.from_user.id)
    await callback.message.edit_text(
        f"🕒 Запланировано на {publish_at.strftime('%d.%m %H:%M')} (МСК). ID: {schedule_id}",
        reply_markup=None,
    )
    await callback.answer()


@router.callback_query(F.data == "sched_pick_day")
async def cb_sched_pick_day(callback: CallbackQuery, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await callback.message.edit_reply_markup(reply_markup=schedule_days_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("sched_day:"))
async def cb_sched_day(callback: CallbackQuery, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    day = callback.data.split(":")[1]
    await callback.message.edit_reply_markup(reply_markup=schedule_times_keyboard(day))
    await callback.answer()


@router.callback_query(F.data.startswith("sched_set:"))
async def cb_sched_set(callback: CallbackQuery, db: Database, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    _, day, hhmm = callback.data.split(":")
    publish_at = datetime.strptime(f"{day}{hhmm}", "%Y%m%d%H%M").replace(tzinfo=TZ)
    if publish_at <= datetime.now(TZ):
        await callback.answer("Это время уже прошло.", show_alert=True)
        return
    schedule_id = await db.schedule_post(
        post_id=int(payload["post_id"]),
        channel_id=config.channel_id,
        post_text=payload["post_text"],
        publish_at=publish_at,
        media_type=payload.get("media_type"),
        media_file_id=payload.get("media_file_id"),
    )
    await redis_client.delete_pending_post(callback.from_user.id)
    await callback.message.edit_text(
        f"🕒 Запланировано на {publish_at.strftime('%d.%m %H:%M')} (МСК). ID: {schedule_id}",
        reply_markup=None,
    )
    await callback.answer()


@router.callback_query(F.data == "sched_back")
async def cb_sched_back(callback: CallbackQuery, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    payload = await redis_client.get_pending_post(callback.from_user.id)
    if not payload:
        await callback.answer("Пост не найден или срок истек.", show_alert=True)
        return
    media_note = "\n\n📎 Медиа будет приложено к публикации." if payload.get("media_type") and payload.get("media_file_id") else ""
    await callback.message.edit_text(
        f"Предпросмотр поста:{media_note}\n\n{format_for_telegram_html(payload['post_text'])}",
        reply_markup=moderation_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "cancel_post")
async def cb_cancel_post(callback: CallbackQuery, redis_client: RedisClient, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    await redis_client.delete_pending_post(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer("Отменено")
    await callback.answer()


@router.callback_query(F.data.startswith("sched_cancel:"))
async def cb_sched_cancel(callback: CallbackQuery, db: Database, config: Config) -> None:
    if not callback.from_user or callback.from_user.id != config.owner_id:
        await callback.answer("Недостаточно прав.", show_alert=True)
        return
    schedule_id = int(callback.data.split(":")[1])
    cancelled = await db.cancel_scheduled(schedule_id)
    if not cancelled:
        await callback.answer("Не удалось отменить (возможно уже опубликовано).", show_alert=True)
        return
    await callback.message.edit_text(f"🗑 Публикация {schedule_id} отменена.")
    await callback.answer("Отменено")
