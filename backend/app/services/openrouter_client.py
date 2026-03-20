"""OpenRouter LLM client — OpenAI-compatible API.

Public API
----------
run_llm(prompt, *, system, model, temperature) -> str
    Plain-text completion with automatic retry.

run_structured_llm(prompt, schema, *, system, model, temperature) -> dict
    JSON completion validated against a Pydantic schema, with retry and
    safe JSON parsing.
"""

import asyncio
import json
import logging
import re
from typing import Any

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

# Retry policy: up to 3 attempts, with exponential back-off between them.
_RETRY_DELAYS = (1.0, 2.0, 4.0)  # seconds between attempt 1→2, 2→3, 3→(fail)


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key or "sk-placeholder",
        )
    return _client


# ── Public API ────────────────────────────────────────────────────────────────

async def run_llm(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
) -> str:
    """Send a prompt and return the raw text response.

    Returns an empty string when mock mode is active, the API key is missing,
    or all retry attempts are exhausted.
    """
    if not settings.openrouter_api_key or settings.use_mock:
        return ""

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_exc: Exception | None = None
    for attempt, delay in enumerate(
        [*_RETRY_DELAYS, None], start=1  # None sentinel → no more retries
    ):
        try:
            resp = await get_client().chat.completions.create(
                model=model or settings.fast_model,
                temperature=temperature,
                messages=messages,
            )
            return resp.choices[0].message.content or ""

        except RateLimitError as exc:
            last_exc = exc
            if delay is not None:
                logger.warning(
                    "[openrouter] rate-limited on attempt %d, retrying in %.0fs", attempt, delay
                )
                await asyncio.sleep(delay)

        except APIConnectionError as exc:
            last_exc = exc
            if delay is not None:
                logger.warning(
                    "[openrouter] connection error on attempt %d, retrying in %.0fs", attempt, delay
                )
                await asyncio.sleep(delay)

        except APIStatusError as exc:
            if exc.status_code >= 500 and delay is not None:
                last_exc = exc
                logger.warning(
                    "[openrouter] server error %d on attempt %d, retrying in %.0fs",
                    exc.status_code, attempt, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error("[openrouter] non-retryable HTTP %d: %s", exc.status_code, exc)
                return ""

        except Exception as exc:
            logger.error("[openrouter] unexpected error: %s", exc)
            return ""

    logger.error(
        "[openrouter] all %d attempts exhausted. last error: %s",
        len(_RETRY_DELAYS) + 1, last_exc,
    )
    return ""


async def run_structured_llm(
    prompt: str,
    schema: type[BaseModel],
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Send a prompt and return a JSON dict conforming to *schema*.

    The JSON schema derived from *schema* is appended to the system prompt so
    the model knows exactly what keys and types to return.  The response is
    parsed with :func:`_safe_parse_json`; returns ``{}`` on failure.
    """
    schema_hint = json.dumps(schema.model_json_schema(), indent=2)
    json_instruction = f"Return ONLY valid JSON conforming to this schema:\n{schema_hint}"
    augmented_system = f"{system}\n\n{json_instruction}" if system else json_instruction

    text = await run_llm(
        prompt,
        system=augmented_system,
        model=model,
        temperature=temperature,
    )
    if not text:
        return {}
    return _safe_parse_json(text)


# ── JSON helpers ──────────────────────────────────────────────────────────────

def _safe_parse_json(text: str) -> dict[str, Any]:
    """Return a dict parsed from *text*, stripping Markdown code fences.

    Falls back to extracting the first ``{…}`` block from mixed-text responses.
    Returns ``{}`` if nothing parseable is found.
    """
    text = text.strip()

    # Strip ```json … ``` or ``` … ``` fences
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    text = text.strip()

    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
        logger.warning("[openrouter] expected JSON object, got %s", type(result).__name__)
        return {}
    except json.JSONDecodeError:
        pass

    # Last resort: grab the first {...} block from a mixed-text response
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("[openrouter] could not parse JSON from response: %.200s", text)
    return {}


# ── Backward-compatible wrapper ───────────────────────────────────────────────

async def chat_json(
    system: str,
    user: str,
    model: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Legacy wrapper kept for backward compatibility.

    Prefer :func:`run_structured_llm` for new code.
    """
    text = await run_llm(user, system=system, model=model, temperature=temperature)
    if not text:
        return {}
    return _safe_parse_json(text)
