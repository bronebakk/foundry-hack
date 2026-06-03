"""InferenceProvider — the single seam between the app and the model.

Speaks the OpenAI-compatible chat API, pointed at OpenRouter today and at a self-hosted
vLLM server in production (decision D-002). Two guarantees live here, both load-bearing
for the invariants:

  * Open-weight only (Invariant 4 / VAL-GOV-002): every call is checked against
    ``ALLOWED_MODELS``. A closed/proprietary model id is refused before any network call.
  * No autonomy (Invariant 1): this class only *generates text*. It never persists,
    sends, or commits anything. Disposition is always a separate, explicit human step
    handled elsewhere (M2's decision_log).
"""
from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app import config


class InferenceError(RuntimeError):
    pass


class ClosedModelRefused(InferenceError):
    """Raised if a non-open-weight model is ever requested — a code-level invariant guard."""


@dataclass
class Completion:
    text: str
    model: str  # the model that actually answered (after any fallback)


class InferenceProvider:
    def __init__(self) -> None:
        self._base_url = config.INFERENCE_BASE_URL
        self._api_key = config.INFERENCE_API_KEY
        self._client: OpenAI | None = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _ensure_client(self) -> OpenAI:
        if not self._api_key:
            raise InferenceError(
                "No inference API key set. Put OPENROUTER_API_KEY in your environment/.env "
                "(stand-in for the self-hosted vLLM key in production)."
            )
        if self._client is None:
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    @staticmethod
    def _guard_open_weight(model: str) -> None:
        if model not in config.ALLOWED_MODELS:
            raise ClosedModelRefused(
                f"Refused: '{model}' is not in the open-weight allowlist {sorted(config.ALLOWED_MODELS)}. "
                "Only open-weight, self-hostable models may enter the inference path (Invariant 4)."
            )

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> Completion:
        """Generate text. Tries the primary open-weight model, falls back to the secondary
        open-weight model on transport error. Both are allowlist-checked."""
        primary = model or config.PRIMARY_MODEL
        self._guard_open_weight(primary)
        client = self._ensure_client()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        candidates = [primary]
        if primary != config.FALLBACK_MODEL:
            candidates.append(config.FALLBACK_MODEL)

        last_err: Exception | None = None
        for candidate in candidates:
            self._guard_open_weight(candidate)
            try:
                resp = client.chat.completions.create(
                    model=candidate,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return Completion(text=resp.choices[0].message.content or "", model=candidate)
            except ClosedModelRefused:
                raise
            except Exception as exc:  # transport/rate/5xx — try the open-weight fallback
                last_err = exc
                continue
        raise InferenceError(f"All open-weight candidates failed: {last_err}")


# Module-level singleton; cheap to import, no network until first ``complete``.
provider = InferenceProvider()
