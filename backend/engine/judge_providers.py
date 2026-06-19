"""Pluggable LLM judge providers for Ozark rubric evaluators.

The default provider is deterministic/offline, which keeps the project
zero-cost and air-gapped.  Users can opt into a remote judge by setting
environment variables:

* ``JUDGE_PROVIDER``      → ``openai`` or ``anthropic`` (selects which SDK to use)
* ``JUDGE_API_KEY``       → API key for the provider
* ``JUDGE_BASE_URL``      → Base URL (optional; defaults to the SDK's built-in endpoint)
* ``JUDGE_MODEL``         → Model name (e.g. ``gpt-4o-mini``, ``claude-3-5-sonnet-20241022``)
* ``JUDGE_CONTEXT_WINDOW``→ Max context tokens (optional; used to truncate long text)

This lets users bring any OpenAI-compatible or Anthropic-compatible endpoint
— OpenAI, Azure, Ollama, vLLM, LiteLLM, Groq, Together, etc. — without
hardcoding provider-specific env vars.

Each provider implements a single method::

    judge(prompt: str, text: str, rubric: str) -> dict[str, Any]

Returning ``{"score": float 0-1, "passed": bool, "reasoning": str}``.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

LOGGER = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT = (
    "You are an exacting evaluator. Score the assistant response against "
    "the rubric on a scale of 0.0 to 1.0. Return ONLY a JSON object with "
    "keys: score (float), passed (bool), reasoning (string). No markdown, "
    "no prose."
)


class JudgeProvider(ABC):
    """Abstract interface for an LLM judge."""

    @abstractmethod
    def judge(
        self,
        *,
        prompt: str,
        text: str,
        rubric: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        """Score ``text`` against ``rubric``.

        Returns a dict with ``score`` (0.0-1.0), ``passed`` (bool), and
        ``reasoning`` (str). Implementations must be safe to call from
        worker threads.
        """
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        raise NotImplementedError


def _truncate_for_context(text: str, context_window: int | None, overhead: int = 600) -> str:
    """Truncate text to fit within the model's context window.

    ``overhead`` accounts for the system prompt, rubric, and user instruction.
    Uses a rough 4-chars-per-token approximation.

    If ``context_window`` is None (user didn't set ``JUDGE_CONTEXT_WINDOW``),
    no truncation is performed — the API will handle token limits.
    """
    if context_window is None:
        return text
    max_chars = max(1, (context_window - overhead) * 4)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n…[truncated]"


class OfflineJudgeProvider(JudgeProvider):
    """Deterministic fallback that scores by simple heuristics.

    Useful for CI, air-gapped environments, and validating the evaluator
    plumbing without spending LLM API credits.
    """

    def is_available(self) -> bool:
        return True

    def judge(
        self,
        *,
        prompt: str,
        text: str,
        rubric: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        rubric_lower = rubric.lower()
        text_lower = text.lower()

        positive_keywords = [
            "correct", "appropriate", "safe", "compliant", "accurate",
            "helpful", "clear", "complete", "relevant", "polite",
        ]
        negative_keywords = [
            "incorrect", "inappropriate", "unsafe", "non-compliant", "inaccurate",
            "harmful", "rude", "incomplete", "irrelevant", "leak",
        ]

        pos = sum(1 for kw in positive_keywords if kw in rubric_lower and kw in text_lower)
        neg = sum(1 for kw in negative_keywords if kw in rubric_lower and kw in text_lower)

        if any(word in rubric_lower for word in ["must include", "should include", "contains"]):
            required = [
                word.strip(".,!?;:")
                for word in rubric_lower.split()
                if len(word) > 5 and word not in positive_keywords
            ][:3]
            for req in required:
                if req in text_lower:
                    pos += 1
                else:
                    neg += 1

        score = max(0.0, min(1.0, 0.7 + (pos * 0.1) - (neg * 0.2)))
        threshold = 0.7
        return {
            "score": round(score, 3),
            "passed": score >= threshold,
            "reasoning": (
                f"Offline heuristic: {pos} positive signals, {neg} negative signals. "
                f"Score {score:.2f} vs threshold {threshold:.2f}."
            ),
        }


class OpenAICompatibleJudgeProvider(JudgeProvider):
    """Judge using any OpenAI-compatible API.

    Works with OpenAI, Azure, Ollama, vLLM, LiteLLM, Groq, Together, etc.
    Requires ``JUDGE_API_KEY`` and ``JUDGE_PROVIDER=openai``.
    """

    def is_available(self) -> bool:
        return (
            os.environ.get("JUDGE_PROVIDER") == "openai"
            and bool(os.environ.get("JUDGE_API_KEY"))
        )

    def judge(
        self,
        *,
        prompt: str,
        text: str,
        rubric: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        try:
            import openai
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc

        model = os.environ.get("JUDGE_MODEL", "gpt-4o-mini")
        base_url = os.environ.get("JUDGE_BASE_URL")
        context_window_raw = os.environ.get("JUDGE_CONTEXT_WINDOW")
        context_window = int(context_window_raw) if context_window_raw else None

        client_kwargs: dict[str, Any] = {"api_key": os.environ["JUDGE_API_KEY"]}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = openai.OpenAI(**client_kwargs)

        text = _truncate_for_context(text, context_window)
        user = f"Rubric:\n{rubric}\n\nResponse to evaluate:\n{text}\n\n{prompt}"
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return _normalize_json_response(content)


class AnthropicCompatibleJudgeProvider(JudgeProvider):
    """Judge using any Anthropic-compatible API.

    Works with Anthropic, or any endpoint that speaks the Anthropic Messages API.
    Requires ``JUDGE_API_KEY`` and ``JUDGE_PROVIDER=anthropic``.
    """

    def is_available(self) -> bool:
        return (
            os.environ.get("JUDGE_PROVIDER") == "anthropic"
            and bool(os.environ.get("JUDGE_API_KEY"))
        )

    def judge(
        self,
        *,
        prompt: str,
        text: str,
        rubric: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> dict[str, Any]:
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("anthropic package is not installed") from exc

        model = os.environ.get("JUDGE_MODEL", "claude-3-5-sonnet-20241022")
        base_url = os.environ.get("JUDGE_BASE_URL")
        context_window_raw = os.environ.get("JUDGE_CONTEXT_WINDOW")
        context_window = int(context_window_raw) if context_window_raw else None

        client_kwargs: dict[str, Any] = {"api_key": os.environ["JUDGE_API_KEY"]}
        if base_url:
            client_kwargs["base_url"] = base_url
        client = anthropic.Anthropic(**client_kwargs)

        text = _truncate_for_context(text, context_window)
        user = f"Rubric:\n{rubric}\n\nResponse to evaluate:\n{text}\n\n{prompt}"
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user}],
        )
        content = resp.content[0].text if resp.content else "{}"
        return _normalize_json_response(content)


def _normalize_json_response(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`").split("\n", 1)[-1].rsplit("\n", 1)[0].strip()
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        LOGGER.warning("Judge returned non-JSON response: %s", content[:200])
        return {"score": 0.0, "passed": False, "reasoning": "judge returned invalid JSON"}

    score = float(parsed.get("score", 0.0))
    passed = bool(parsed.get("passed", score >= 0.7))
    reasoning = str(parsed.get("reasoning", "no reasoning provided"))
    return {"score": max(0.0, min(1.0, round(score, 3))), "passed": passed, "reasoning": reasoning}


_JUDGE_PROVIDERS: list[JudgeProvider] = []


def get_judge_provider() -> JudgeProvider:
    """Return the configured judge provider, or the offline fallback.

    Selection order:
    1. ``JUDGE_PROVIDER=openai``   → OpenAI-compatible provider
    2. ``JUDGE_PROVIDER=anthropic`` → Anthropic-compatible provider
    3. Offline heuristic fallback
    """
    global _JUDGE_PROVIDERS
    if not _JUDGE_PROVIDERS:
        _JUDGE_PROVIDERS = [
            OpenAICompatibleJudgeProvider(),
            AnthropicCompatibleJudgeProvider(),
            OfflineJudgeProvider(),
        ]
    for provider in _JUDGE_PROVIDERS:
        if provider.is_available():
            return provider
    return OfflineJudgeProvider()


def reset_judge_providers() -> None:
    """Reset the provider cache (useful in tests)."""
    global _JUDGE_PROVIDERS
    _JUDGE_PROVIDERS = []
