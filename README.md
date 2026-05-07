# unlimyFlow

[![CI](https://github.com/OWNER/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
[![CD](https://github.com/OWNER/REPO/actions/workflows/cd.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/cd.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)

Production-ready Telegram-бот для редакционного пайплайна Unlimy: принимает новость, генерирует пост через LLM, отправляет на модерацию, публикует сразу или по расписанию.

## Ключевые возможности
- Генерация постов через OpenAI (`generate -> rule-based validate -> critic`).
- Очистка пересланных сообщений от ссылочного/рекламного мусора.
- Режимы публикации:
  - `instant` — публикация сразу в канал.
  - `queue` — предпросмотр и модерация.
- Модерация через inline-кнопки:
  - `Опубликовать сейчас`
  - `Перегенерировать`
  - `Запланировать` (интервалы, день, время)
  - `Отмена`
- Фоновый воркер отложенных публикаций.
- `/scheduled` — просмотр и отмена запланированных постов.
- PostgreSQL для истории и очередей.
- Redis для временных ключей и флагов.
- Логирование в файл + stdout.

## Архитектура
- `main.py` — запуск бота, DI зависимостей, воркер scheduled-публикаций.
- `handlers.py` — команды, сообщения, callback-логика.
- `llm.py` — генератор, rule-based валидатор, critic-pass.
- `formatter.py` — финальный рендер под Telegram HTML.
- `db.py` — asyncpg-слой (posts + scheduled_posts).
- `redis_client.py` — pending посты/режим/счетчики.
- `cleaner.py` — очистка форвардов.
- `keyboards.py` — inline-клавиатуры модерации и расписания.
- `config.py` — env-конфиг.

## Требования
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- OpenAI API key

## Быстрый старт (локально)
1. Установите зависимости:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
2. Поднимите БД/Redis:
```bash
docker compose up -d
```
3. Подготовьте env:
```bash
cp .env.example .env
```
4. Запустите бота:
```bash
python main.py
```

## Переменные окружения
Минимально обязательные:
- `BOT_TOKEN`
- `OWNER_ID`
- `CHANNEL_ID`
- `OPENAI_API_KEY`
- `PG_DSN`
- `REDIS_URL`

LLM-параметры:
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `OPENAI_MODEL_CRITIC` (default = `OPENAI_MODEL`)
- `TEMPERATURE_GENERATOR`
- `TEMPERATURE_CRITIC`
- `MAX_TOKENS_GENERATOR`
- `MAX_TOKENS_CRITIC`
- `MAX_RETRIES`

Прочее:
- `PUBLISH_MODE` (`instant` / `queue`)
- `LOG_DIR`
- `CUSTOM_STAR_EMOJI_ID` (опционально, custom emoji для CTA)

## Команды бота
- `/start`
- `/help`
- `/mode`
- `/status`
- `/history`
- `/scheduled`

## Production Deploy (VPS, Docker Compose)
### 1) Подготовка сервера
- Ubuntu 22.04+ (рекомендуется)
- Установить Docker + Compose plugin
- Открыть firewall для SSH

### 2) Клонирование и env
```bash
git clone <your-repo-url> ~/unlimyFlow
cd ~/unlimyFlow
cp deploy/.env.prod.example .env.prod
```
Заполните `.env.prod`.

### 3) Запуск
```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 4) Обновление
```bash
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod up -d --build
```

## CI/CD
Репозиторий содержит GitHub Actions:
- `CI` (`.github/workflows/ci.yml`)
  - установка зависимостей
  - проверка импорта/синтаксиса (`compileall`)
- `CD` (`.github/workflows/cd.yml`)
  - деплой на VPS по SSH при push в `main` или вручную.

### Secrets для CD
Добавьте в GitHub repository secrets:
- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `VPS_PORT` (опционально, default `22`)
- `VPS_APP_DIR` (опционально, default `~/unlimyFlow`)

## Наблюдаемость
- Логи: `logs/unlimy_flow.log`
- Проверка контейнеров:
```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod ps
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod logs -f bot
```
