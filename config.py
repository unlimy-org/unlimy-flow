from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Config:
    bot_token: str
    owner_id: int
    channel_id: str
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_model_critic: str = "gpt-4o-mini"
    temperature_generator: float = 0.7
    temperature_critic: float = 0.3
    max_tokens_generator: int = 1500
    max_tokens_critic: int = 1500
    publish_mode: str = "queue"
    max_retries: int = 3
    pg_dsn: str = "postgresql://postgres:postgres@localhost:5432/unlimyflow"
    redis_url: str = "redis://localhost:6379/0"
    log_dir: str = "logs"


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def _normalize_channel_id(value: str) -> str:
    raw = value.strip()
    if raw.startswith("@"):
        return raw

    if raw.lstrip("-").isdigit():
        if raw.startswith("-100"):
            return raw
        if raw.startswith("-"):
            return raw
        # Telegram channel numeric IDs are usually negative with -100 prefix.
        return f"-100{raw}"

    return raw


def load_config() -> Config:
    load_dotenv()

    publish_mode = os.getenv("PUBLISH_MODE", "queue").strip().lower()
    if publish_mode not in {"instant", "queue"}:
        publish_mode = "queue"

    log_dir = os.getenv("LOG_DIR", "logs")
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    return Config(
        bot_token=_require("BOT_TOKEN"),
        owner_id=int(_require("OWNER_ID")),
        channel_id=_normalize_channel_id(_require("CHANNEL_ID")),
        openai_api_key=_require("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_model_critic=os.getenv("OPENAI_MODEL_CRITIC", os.getenv("OPENAI_MODEL", "gpt-4o-mini")),
        temperature_generator=float(os.getenv("TEMPERATURE_GENERATOR", "0.7")),
        temperature_critic=float(os.getenv("TEMPERATURE_CRITIC", "0.3")),
        max_tokens_generator=int(os.getenv("MAX_TOKENS_GENERATOR", "1500")),
        max_tokens_critic=int(os.getenv("MAX_TOKENS_CRITIC", "1500")),
        publish_mode=publish_mode,
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        pg_dsn=_require("PG_DSN"),
        redis_url=_require("REDIS_URL"),
        log_dir=log_dir,
    )
