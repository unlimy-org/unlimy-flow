from __future__ import annotations

import html
import os
import re

TITLE_PREFIX_RE = re.compile(r"^\s*(заголовок|title)\s*:\s*", flags=re.IGNORECASE)
MD_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
MD_DECOR_RE = re.compile(r"(\*\*|__|`)")
BULLET_RE = re.compile(r"^\s*[-•]\s+")
RAW_TME_RE = re.compile(r"\(?\s*(?:https?://)?t\.me/[A-Za-z0-9_]+\s*\)?", flags=re.IGNORECASE)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
TRAILING_BRAND_RE = re.compile(r"^\s*unlimy\s*\.?\s*$", flags=re.IGNORECASE)
CTA_LINE_RE = re.compile(r"(для пользователей unlimy|попробуйте бесплатно 3 дня|@unlimy_?bot|t\.me/unlimy)", flags=re.IGNORECASE)
STYLE_NOISE_RE = re.compile(
    r"(интересно,\s*что\s*из\s*этого\s*выйдет\.?|"
    r"в\s*общем,\s*если\s*вы\s*думали[^.?!]*[.?!]|"
    r"интересно,\s*как\s*будут\s*развиваться\s*события\.?|"
    r"следите\s*за\s*новостями!?\.?)",
    flags=re.IGNORECASE,
)
def _get_custom_star_emoji_id() -> str:
    # Read at runtime so .env values loaded in load_config() are visible.
    return os.getenv("CUSTOM_STAR_EMOJI_ID", "").strip()


def _normalize_line(line: str) -> str:
    line = line.rstrip()
    line = TITLE_PREFIX_RE.sub("", line)
    line = MD_HEADER_RE.sub("", line)
    line = MD_DECOR_RE.sub("", line)
    line = BULLET_RE.sub("• ", line)
    line = RAW_TME_RE.sub("", line).strip()
    return line


def _split_long_paragraphs(lines: list[str], max_len: int = 165) -> list[str]:
    out: list[str] = []
    for line in lines:
        if not line.strip() or len(line) <= max_len:
            out.append(line)
            continue
        parts = SENTENCE_SPLIT_RE.split(line)
        chunk = ""
        for part in parts:
            candidate = (chunk + " " + part).strip()
            if len(candidate) <= max_len:
                chunk = candidate
            else:
                if chunk:
                    out.append(chunk)
                chunk = part.strip()
        if chunk:
            out.append(chunk)
    return out


def _drop_trailing_noise(lines: list[str]) -> list[str]:
    while lines and not lines[-1].strip():
        lines.pop()
    while lines and TRAILING_BRAND_RE.match(lines[-1]):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    return lines


def _strip_existing_cta(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        if CTA_LINE_RE.search(line):
            continue
        cleaned.append(line)
    return cleaned


def _strip_style_noise(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        cleaned = STYLE_NOISE_RE.sub("", line).strip()
        if cleaned:
            out.append(cleaned)
        else:
            out.append("")
    return out


def _compress_paragraph_count(lines: list[str], max_paragraphs: int = 4) -> list[str]:
    paragraphs: list[str] = []
    cur: list[str] = []
    for line in lines:
        if not line.strip():
            if cur:
                paragraphs.append(" ".join(cur).strip())
                cur = []
            continue
        cur.append(line.strip())
    if cur:
        paragraphs.append(" ".join(cur).strip())

    if len(paragraphs) <= max_paragraphs:
        out: list[str] = []
        for p in paragraphs:
            out.append(p)
            out.append("")
        return out[:-1] if out else out

    # Склеиваем хвостовые абзацы, сохраняя заголовок отдельно.
    head = paragraphs[:1]
    tail = paragraphs[1:]
    while len(head) + len(tail) > max_paragraphs:
        tail[-2] = f"{tail[-2]} {tail[-1]}".strip()
        tail.pop()
    merged = head + tail

    out: list[str] = []
    for p in merged:
        out.append(p)
        out.append("")
    return out[:-1]


def _canonical_cta_html() -> str:
    custom_star_emoji_id = _get_custom_star_emoji_id()
    star = (
        f'<tg-emoji emoji-id="{html.escape(custom_star_emoji_id)}">⭐️</tg-emoji>'
        if custom_star_emoji_id
        else "⭐️"
    )
    return (
        f"{star} <b>Для пользователей Unlimy ничего не меняется. "
        "Наш сервис работает при любых сценариях ограничений.</b>\n"
        '<b><a href="https://t.me/unlimy_vpn">Попробуйте бесплатно 3 дня</a></b>.'
    )


def format_for_telegram_html(text: str) -> str:
    lines = [_normalize_line(line) for line in text.splitlines()]
    lines = _split_long_paragraphs(lines)
    lines = _strip_style_noise(lines)
    lines = _strip_existing_cta(lines)
    lines = _drop_trailing_noise(lines)
    lines = _compress_paragraph_count(lines, max_paragraphs=4)

    first_idx = next((i for i, line in enumerate(lines) if line.strip()), -1)
    rendered: list[str] = []
    for i, line in enumerate(lines):
        esc = html.escape(line)
        if i == first_idx and line.strip():
            rendered.append(f"<b>{esc}</b>")
        else:
            rendered.append(esc)

    body = "\n".join(rendered).strip()
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    if body:
        return f"{body}\n\n{_canonical_cta_html()}"
    return _canonical_cta_html()
