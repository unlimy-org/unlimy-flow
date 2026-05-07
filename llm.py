from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, RateLimitError

from config import Config

SYSTEM_PROMPT = """
Ты — редактор Telegram-канала Unlimy (@unlimy_bot).
Пиши живо, по-человечески, с легкой иронией, без канцелярита и пафоса.

Требования:
1) Короткий заголовок (5-8 слов), не начинай с "Заголовок:".
2) Текст разбивай на короткие абзацы: 1-2 предложения в абзаце.
3) Всего абзацев до CTA: 3-4 (не больше).
4) Без markdown-символов: *, _, #, `, >.
5) Без хештегов и без дисклеймера.
6) Не заканчивай пост многоточием.
7) Если новость не про технические блокировки в РФ/СНГ — не пиши блок про "частичные ограничения / блэкаут".
8) Избегай штампов и фраз вроде: "Печально, не так ли?", "эстафета передана", "мяч на их стороне".
9) Тон: экспертный, понятный, без "душных" формулировок.
10) Длина до 1800 символов.
""".strip()

CRITIC_PROMPT = """
Ты — строгий редактор-валидатор.
Исправь черновик так, чтобы:
- тон был живой и современный (без канцелярита),
- абзацы были короткие,
- абзацев до CTA было не больше 4,
- не было markdown-символов, хештегов и дисклеймера,
- не было штампов: "Печально, не так ли?", "эстафета передана", "мяч на их стороне",
- текст был цельным и заканчивался точкой.
Верни только итоговый текст.
""".strip()


@dataclass(slots=True)
class ValidationResult:
    passed: bool
    violations: list[str]


class LLMClient:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._openai_client = AsyncOpenAI(api_key=config.openai_api_key)
        self._forbidden_markdown_chars = ["*", "_", "#", "`", ">"]
        self._forbidden_phrases = [
            "в настоящее время",
            "в случае реализации",
            "вызывает множество вопросов",
            "может вызвать опасения",
            "представляет собой",
            "печально, не так ли",
            "эстафета передана",
            "мяч на их стороне",
            "интересно, что из этого выйдет",
            "в общем, если вы думали",
            "интересно, как будут развиваться события",
            "следите за новостями",
        ]

    async def _call_openai(self, prompt: str, *, model: str, temperature: float, max_tokens: int, system: str) -> str:
        response = await self._openai_client.responses.create(
            model=model,
            instructions=system,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return (response.output_text or "").strip()

    async def _call_llm(self, prompt: str, *, system: str, critic: bool = False) -> str:
        model = self._config.openai_model_critic if critic else self._config.openai_model
        temperature = self._config.temperature_critic if critic else self._config.temperature_generator
        max_tokens = self._config.max_tokens_critic if critic else self._config.max_tokens_generator
        return await self._call_openai(prompt, model=model, temperature=temperature, max_tokens=max_tokens, system=system)

    async def generate_post(self, news_text: str, metadata: dict[str, Any]) -> str:
        prompt = (
            f"Метаданные:\n{json.dumps(metadata, ensure_ascii=False)}\n\n"
            f"Новость:\n{news_text}\n\n"
            "Сгенерируй пост по правилам."
        )
        return await self._call_llm(prompt, system=SYSTEM_PROMPT, critic=False)

    def rule_based_validator(self, post: str, metadata: dict[str, Any], max_len: int = 1800) -> ValidationResult:
        violations: list[str] = []
        text = (post or "").strip()
        low = text.lower()

        if len(text) > max_len:
            violations.append(f"Длина превышает {max_len}")
        for ch in self._forbidden_markdown_chars:
            if ch in text:
                violations.append(f"Запрещённый markdown символ: {ch}")
        for phrase in self._forbidden_phrases:
            if phrase in low:
                violations.append(f"Канцелярит: {phrase}")
        if re.search(r"(?:\.{3}|…)\s*$", text):
            violations.append("Пост заканчивается многоточием")
        if "дисклеймер" in low or "это не паника" in low:
            violations.append("Дисклеймер не нужен")

        is_tech = bool(metadata.get("is_technical_blocking_in_russia", False))
        if not is_tech:
            if re.search(r"частичны[её]\s+ограничени[яе]", low) or re.search(r"полн[ыуй]\s+блэкаут", low) or re.search(r"два\s+сценария", low):
                violations.append("Неуместные сценарии для не-технической новости")
        return ValidationResult(passed=not violations, violations=violations)

    async def llm_critic(self, post: str, violations: list[str], metadata: dict[str, Any]) -> str:
        prompt = (
            f"{CRITIC_PROMPT}\n\n"
            f"Черновик:\n{post}\n\n"
            f"Нарушения:\n{json.dumps(violations, ensure_ascii=False)}\n\n"
            f"Метаданные:\n{json.dumps(metadata, ensure_ascii=False)}"
        )
        return await self._call_llm(prompt, system=CRITIC_PROMPT, critic=True)

    async def process_news(
        self,
        news_text: str,
        metadata: dict[str, Any],
        *,
        max_len: int = 1800,
        critic_passes: int = 1,
    ) -> tuple[str, list[str]]:
        delays = [2, 4, 8]
        attempts = max(self._config.max_retries, 1)

        for attempt in range(1, attempts + 1):
            try:
                post = await self.generate_post(news_text, metadata)
                res = self.rule_based_validator(post, metadata, max_len=max_len)
                if res.passed:
                    return post, []

                self._logger.warning("Violations after generate: %s", res.violations)
                current_post = post
                current_violations = res.violations

                for _ in range(max(critic_passes, 0)):
                    current_post = await self.llm_critic(current_post, current_violations, metadata)
                    recheck = self.rule_based_validator(current_post, metadata, max_len=max_len)
                    if recheck.passed:
                        return current_post, []
                    current_violations = recheck.violations
                    self._logger.warning("Violations after critic pass: %s", current_violations)
                return current_post, current_violations
            except (RateLimitError, APITimeoutError, APIConnectionError, TimeoutError):
                self._logger.exception("Retriable LLM error on attempt=%s", attempt)
                if attempt >= attempts:
                    raise
                await asyncio.sleep(delays[min(attempt - 1, len(delays) - 1)])
            except Exception:
                self._logger.exception("Non-retriable LLM error on attempt=%s", attempt)
                raise
