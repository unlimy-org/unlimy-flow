from __future__ import annotations

import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config, load_config
from db import Database
from formatter import format_for_telegram_html
from handlers import router
from llm import LLMClient
from middlewares import OwnerOnlyMiddleware
from redis_client import RedisClient


def setup_logging(log_dir: str) -> None:
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        filename=f"{log_dir}/unlimy_flow.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)


async def run() -> None:
    config: Config = load_config()
    setup_logging(config.log_dir)
    logger = logging.getLogger(__name__)

    db = Database(config.pg_dsn)
    redis_client = RedisClient(config.redis_url)
    llm = LLMClient(config)

    await db.connect()
    await redis_client.connect()

    if not await redis_client.raw.exists("publish_mode"):
        await redis_client.set_publish_mode(config.publish_mode)

    mode = await redis_client.get_publish_mode(config.publish_mode)
    logger.info("Bot started with mode=%s, channel=%s", mode, config.channel_id)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.middleware(OwnerOnlyMiddleware(config.owner_id))
    dp.include_router(router)

    async def _publish_scheduled_once() -> None:
        rows = await db.fetch_due_scheduled(limit=20)
        for row in rows:
            try:
                formatted = format_for_telegram_html(row["post_text"])
                media_type = row["media_type"]
                media_file_id = row["media_file_id"]
                if media_type == "photo" and media_file_id:
                    await bot.send_photo(chat_id=row["channel_id"], photo=media_file_id, caption=formatted[:1024])
                elif media_type == "video" and media_file_id:
                    await bot.send_video(chat_id=row["channel_id"], video=media_file_id, caption=formatted[:1024])
                else:
                    await bot.send_message(chat_id=row["channel_id"], text=formatted)
                await db.mark_published(int(row["post_id"]))
                await db.mark_scheduled_done(int(row["id"]))
                logger.info("Scheduled post published: schedule_id=%s post_id=%s", row["id"], row["post_id"])
            except TelegramBadRequest:
                logger.exception("Failed scheduled publish: schedule_id=%s", row["id"])
                await db.mark_scheduled_failed(int(row["id"]))
            except Exception:
                logger.exception("Unexpected error in scheduled publish: schedule_id=%s", row["id"])
                await db.mark_scheduled_failed(int(row["id"]))

    async def _scheduled_worker(stop_event: asyncio.Event) -> None:
        logger.info("Scheduled worker started")
        while not stop_event.is_set():
            try:
                await _publish_scheduled_once()
            except Exception:
                logger.exception("Scheduled worker iteration failed")
            await asyncio.sleep(20)
        logger.info("Scheduled worker stopped")

    stop_event = asyncio.Event()
    worker_task = asyncio.create_task(_scheduled_worker(stop_event))

    async def _on_shutdown() -> None:
        logger.info("Shutting down bot...")
        stop_event.set()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        await db.close()
        await redis_client.close()
        await bot.session.close()

    dp.shutdown.register(_on_shutdown)

    await dp.start_polling(
        bot,
        db=db,
        redis_client=redis_client,
        llm=llm,
        config=config,
    )


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        pass
