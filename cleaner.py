from __future__ import annotations

import re

_BLOCK_PATTERNS = [
    "подписаться",
    "подписывайтесь",
    "источник:",
    "прислали:",
    "реклама",
    "при поддержке",
    "наш спонсор",
    "читать полностью",
    "продолжение в",
]

_TELEGRAM_LINK_RE = re.compile(r"https?://t\.me/[^\s]+", flags=re.IGNORECASE)
_ONLY_EMOJI_OR_SPACE_RE = re.compile(
    r"^[\s\U0001F300-\U0001FAFF\u2600-\u27BF\ufe0f]+$",
    flags=re.UNICODE,
)
_MULTI_BREAKS_RE = re.compile(r"\n{3,}")


def _remove_tg_links(line: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        url = match.group(0).lower()
        return match.group(0) if "@unlimy_bot" in url else ""

    return _TELEGRAM_LINK_RE.sub(_replace, line)


def clean_forwarded_text(text: str) -> str:
    if not text:
        return ""

    cleaned_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if any(pattern in lowered for pattern in _BLOCK_PATTERNS):
            continue

        line = _remove_tg_links(line).strip()
        if not line:
            continue

        if _ONLY_EMOJI_OR_SPACE_RE.fullmatch(line):
            continue

        cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    result = _MULTI_BREAKS_RE.sub("\n\n", result)
    return result
