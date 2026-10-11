"""Structured LLM calls for the crew agents.

One entry point: `complete_json(system, prompt, Model) -> Model | None`.
  - the LLM is AI's hook (`providers.llm()`, text in / text out) when registered, else Gemini via GEMINI_API_KEY;
  - the reply must be JSON matching `Model`; one repair retry, then None (callers fall back to deterministic content);
  - None also means "no LLM configured". Provider errors are logged by type only (they can contain secrets).
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .. import config, providers

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

RETRIES = 2
RETRY_BACKOFF_S = 1.0
CALL_TIMEOUT_MS = 60_000
TRANSIENT_CODES = {429, 500, 502, 503, 504}
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.I)


_quota_until = 0.0
last_failure: str | None = None  # human-readable reason the last call produced no model text (None = fine / no call yet)


def failure_note() -> str | None:
    return last_failure


def available() -> bool:
    return providers.llm() is not None or bool(config.GEMINI_API_KEY)


def _gemini(system: str, prompt: str) -> str | None:
    if not config.GEMINI_API_KEY:
        return None
    from google import genai  # lazy: only needed when a key is configured
    from google.genai import types
    client = genai.Client(api_key=config.GEMINI_API_KEY, http_options={"timeout": CALL_TIMEOUT_MS})
    cfg = types.GenerateContentConfig(system_instruction=system, temperature=0.2, response_mime_type="application/json")
    global _quota_until, last_failure
    if time.monotonic() < _quota_until:  # daily quota already exhausted: fail fast instead of burning retries
        raise RuntimeError("quota")
    for attempt in range(RETRIES + 1):
        try:
            text = getattr(client.models.generate_content(model=config.GEMINI_MODEL, contents=prompt, config=cfg),
                           "text", None)
            return text.strip() if text and text.strip() else ""
        except Exception as exc:  # noqa: BLE001
            code = getattr(exc, "code", None)
            if code == 429 and "PerDay" in str(exc):
                _quota_until = time.monotonic() + 600
                last_failure = "AI model daily quota exceeded (Gemini free tier). Showing basic content; try again later or use another API key / model."
                raise
            if (code in TRANSIENT_CODES or isinstance(exc, TimeoutError)) and attempt < RETRIES:
                time.sleep(RETRY_BACKOFF_S * (2 ** attempt))
                continue
            log.warning("crew Gemini error code=%s type=%s", code, type(exc).__name__)
            raise


def _raw(system: str, prompt: str) -> str | None:
    hook = providers.llm()
    if hook is not None:
        return hook(system + "\n\n" + prompt)
    return _gemini(system, prompt)


def _parse(text: str, model: type[T]) -> T:
    body = _FENCE.sub("", (text or "").strip())
    start, end = body.find("{"), body.rfind("}")
    if start != -1 and end > start:
        body = body[start:end + 1]
    return model.model_validate(json.loads(body))


def complete_json(system: str, prompt: str, model: type[T]) -> T | None:
    schema = json.dumps(model.model_json_schema(), separators=(",", ":"))
    full = (f"{prompt}\n\nReply with ONE JSON object only (no prose, no markdown fences) that validates against this "
            f"JSON schema:\n{schema}")
    text = None
    for attempt in range(2):
        try:
            text = _raw(system, full if attempt == 0 else full + "\n\nYour previous reply was not valid JSON for the schema. Reply with valid JSON only.")
        except Exception as exc:  # noqa: BLE001
            global last_failure
            log.warning("crew LLM call failed: %s", type(exc).__name__)
            if not (last_failure or "").startswith("AI model daily"):
                last_failure = "AI model unavailable (" + type(exc).__name__ + ")."
            return None
        if text is None:
            return None
        try:
            last_failure = None
            return _parse(text, model)
        except (ValueError, ValidationError):
            continue
    log.info("crew LLM reply was not valid %s JSON", model.__name__)
    return None
