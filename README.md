# unlimyFlow

[![CI](https://github.com/unlimy-org/unlimy-flow/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/unlimy-org/unlimy-flow/actions/workflows/ci.yml)
[![CD](https://github.com/unlimy-org/unlimy-flow/actions/workflows/cd.yml/badge.svg?branch=main)](https://github.com/unlimy-org/unlimy-flow/actions/workflows/cd.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-2CA5E0?logo=telegram&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![CI Platform](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![CD Strategy](https://img.shields.io/badge/CD-SSH_Deploy-0A0A0A?logo=github&logoColor=white)

![UnlimyFlow Hero](assets/unlimyflow-hero.png)

Production-ready Telegram-Р±РѕС‚ РґР»СЏ СЂРµРґР°РєС†РёРѕРЅРЅРѕРіРѕ РїР°Р№РїР»Р°Р№РЅР° Unlimy: РїСЂРёРЅРёРјР°РµС‚ РЅРѕРІРѕСЃС‚СЊ, РіРµРЅРµСЂРёСЂСѓРµС‚ РїРѕСЃС‚ С‡РµСЂРµР· LLM, РѕС‚РїСЂР°РІР»СЏРµС‚ РЅР° РјРѕРґРµСЂР°С†РёСЋ, РїСѓР±Р»РёРєСѓРµС‚ СЃСЂР°Р·Сѓ РёР»Рё РїРѕ СЂР°СЃРїРёСЃР°РЅРёСЋ.

## РљР»СЋС‡РµРІС‹Рµ РІРѕР·РјРѕР¶РЅРѕСЃС‚Рё
- Р“РµРЅРµСЂР°С†РёСЏ РїРѕСЃС‚РѕРІ С‡РµСЂРµР· OpenAI (`generate -> rule-based validate -> critic`).
- РћС‡РёСЃС‚РєР° РїРµСЂРµСЃР»Р°РЅРЅС‹С… СЃРѕРѕР±С‰РµРЅРёР№ РѕС‚ СЃСЃС‹Р»РѕС‡РЅРѕРіРѕ/СЂРµРєР»Р°РјРЅРѕРіРѕ РјСѓСЃРѕСЂР°.
- Р РµР¶РёРјС‹ РїСѓР±Р»РёРєР°С†РёРё:
  - `instant` вЂ” РїСѓР±Р»РёРєР°С†РёСЏ СЃСЂР°Р·Сѓ РІ РєР°РЅР°Р».
  - `queue` вЂ” РїСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ Рё РјРѕРґРµСЂР°С†РёСЏ.
- РњРѕРґРµСЂР°С†РёСЏ С‡РµСЂРµР· inline-РєРЅРѕРїРєРё:
  - `РћРїСѓР±Р»РёРєРѕРІР°С‚СЊ СЃРµР№С‡Р°СЃ`
  - `РџРµСЂРµРіРµРЅРµСЂРёСЂРѕРІР°С‚СЊ`
  - `Р—Р°РїР»Р°РЅРёСЂРѕРІР°С‚СЊ` (РёРЅС‚РµСЂРІР°Р»С‹, РґРµРЅСЊ, РІСЂРµРјСЏ)
  - `РћС‚РјРµРЅР°`
- Р¤РѕРЅРѕРІС‹Р№ РІРѕСЂРєРµСЂ РѕС‚Р»РѕР¶РµРЅРЅС‹С… РїСѓР±Р»РёРєР°С†РёР№.
- `/scheduled` вЂ” РїСЂРѕСЃРјРѕС‚СЂ Рё РѕС‚РјРµРЅР° Р·Р°РїР»Р°РЅРёСЂРѕРІР°РЅРЅС‹С… РїРѕСЃС‚РѕРІ.
- PostgreSQL РґР»СЏ РёСЃС‚РѕСЂРёРё Рё РѕС‡РµСЂРµРґРµР№.
- Redis РґР»СЏ РІСЂРµРјРµРЅРЅС‹С… РєР»СЋС‡РµР№ Рё С„Р»Р°РіРѕРІ.
- Р›РѕРіРёСЂРѕРІР°РЅРёРµ РІ С„Р°Р№Р» + stdout.

## РђСЂС…РёС‚РµРєС‚СѓСЂР°
- `main.py` вЂ” Р·Р°РїСѓСЃРє Р±РѕС‚Р°, DI Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№, РІРѕСЂРєРµСЂ scheduled-РїСѓР±Р»РёРєР°С†РёР№.
- `handlers.py` вЂ” РєРѕРјР°РЅРґС‹, СЃРѕРѕР±С‰РµРЅРёСЏ, callback-Р»РѕРіРёРєР°.
- `llm.py` вЂ” РіРµРЅРµСЂР°С‚РѕСЂ, rule-based РІР°Р»РёРґР°С‚РѕСЂ, critic-pass.
- `formatter.py` вЂ” С„РёРЅР°Р»СЊРЅС‹Р№ СЂРµРЅРґРµСЂ РїРѕРґ Telegram HTML.
- `db.py` вЂ” asyncpg-СЃР»РѕР№ (posts + scheduled_posts).
- `redis_client.py` вЂ” pending РїРѕСЃС‚С‹/СЂРµР¶РёРј/СЃС‡РµС‚С‡РёРєРё.
- `cleaner.py` вЂ” РѕС‡РёСЃС‚РєР° С„РѕСЂРІР°СЂРґРѕРІ.
- `keyboards.py` вЂ” inline-РєР»Р°РІРёР°С‚СѓСЂС‹ РјРѕРґРµСЂР°С†РёРё Рё СЂР°СЃРїРёСЃР°РЅРёСЏ.
- `config.py` вЂ” env-РєРѕРЅС„РёРі.

## РўСЂРµР±РѕРІР°РЅРёСЏ
- Python 3.11+
- PostgreSQL 14+
- Redis 6+
- OpenAI API key

## Р‘С‹СЃС‚СЂС‹Р№ СЃС‚Р°СЂС‚ (Р»РѕРєР°Р»СЊРЅРѕ)
1. РЈСЃС‚Р°РЅРѕРІРёС‚Рµ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё:
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
2. РџРѕРґРЅРёРјРёС‚Рµ Р‘Р”/Redis:
```bash
docker compose up -d
```
3. РџРѕРґРіРѕС‚РѕРІСЊС‚Рµ env:
```bash
cp .env.example .env
```
4. Р—Р°РїСѓСЃС‚РёС‚Рµ Р±РѕС‚Р°:
```bash
python main.py
```

## РџРµСЂРµРјРµРЅРЅС‹Рµ РѕРєСЂСѓР¶РµРЅРёСЏ
РњРёРЅРёРјР°Р»СЊРЅРѕ РѕР±СЏР·Р°С‚РµР»СЊРЅС‹Рµ:
- `BOT_TOKEN`
- `OWNER_ID`
- `CHANNEL_ID`
- `OPENAI_API_KEY`
- `PG_DSN`
- `REDIS_URL`

LLM-РїР°СЂР°РјРµС‚СЂС‹:
- `OPENAI_MODEL` (default `gpt-4o-mini`)
- `OPENAI_MODEL_CRITIC` (default = `OPENAI_MODEL`)
- `TEMPERATURE_GENERATOR`
- `TEMPERATURE_CRITIC`
- `MAX_TOKENS_GENERATOR`
- `MAX_TOKENS_CRITIC`
- `MAX_RETRIES`

РџСЂРѕС‡РµРµ:
- `PUBLISH_MODE` (`instant` / `queue`)
- `LOG_DIR`
- `CUSTOM_STAR_EMOJI_ID` (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ, custom emoji РґР»СЏ CTA)

## РљРѕРјР°РЅРґС‹ Р±РѕС‚Р°
- `/start`
- `/help`
- `/mode`
- `/status`
- `/history`
- `/scheduled`

## Production Deploy (VPS, Docker Compose)
### 1) РџРѕРґРіРѕС‚РѕРІРєР° СЃРµСЂРІРµСЂР°
- Ubuntu 22.04+ (СЂРµРєРѕРјРµРЅРґСѓРµС‚СЃСЏ)
- РЈСЃС‚Р°РЅРѕРІРёС‚СЊ Docker + Compose plugin
- РћС‚РєСЂС‹С‚СЊ firewall РґР»СЏ SSH

### 2) РљР»РѕРЅРёСЂРѕРІР°РЅРёРµ Рё env
```bash
git clone <your-repo-url> ~/unlimyFlow
cd ~/unlimyFlow
cp deploy/.env.prod.example .env.prod
```
Р—Р°РїРѕР»РЅРёС‚Рµ `.env.prod`.

### 3) Р—Р°РїСѓСЃРє
```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod up -d --build
```

### 4) РћР±РЅРѕРІР»РµРЅРёРµ
```bash
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod up -d --build
```

## CI/CD
Р РµРїРѕР·РёС‚РѕСЂРёР№ СЃРѕРґРµСЂР¶РёС‚ GitHub Actions:
- `CI` (`.github/workflows/ci.yml`)
  - СѓСЃС‚Р°РЅРѕРІРєР° Р·Р°РІРёСЃРёРјРѕСЃС‚РµР№
  - РїСЂРѕРІРµСЂРєР° РёРјРїРѕСЂС‚Р°/СЃРёРЅС‚Р°РєСЃРёСЃР° (`compileall`)
- `CD` (`.github/workflows/cd.yml`)
  - РґРµРїР»РѕР№ РЅР° VPS РїРѕ SSH РїСЂРё push РІ `main` РёР»Рё РІСЂСѓС‡РЅСѓСЋ.

### Secrets РґР»СЏ CD
Р”РѕР±Р°РІСЊС‚Рµ РІ GitHub repository secrets:
- `VPS_HOST`
- `VPS_USER`
- `VPS_SSH_KEY`
- `VPS_PORT` (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ, default `22`)
- `VPS_APP_DIR` (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ, default `~/unlimyFlow`)

## РќР°Р±Р»СЋРґР°РµРјРѕСЃС‚СЊ
- Р›РѕРіРё: `logs/unlimy_flow.log`
- РџСЂРѕРІРµСЂРєР° РєРѕРЅС‚РµР№РЅРµСЂРѕРІ:
```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod ps
docker compose -f deploy/docker-compose.prod.yml --env-file .env.prod logs -f bot
```
