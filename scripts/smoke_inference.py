"""Inference smoke test (M1 gate). Confirms the open-weight model answers through the
InferenceProvider. Reports cleanly (exit 0) when no API key is set, so the build isn't
blocked on having the key locally.

Run:  python -m scripts.smoke_inference
"""
from __future__ import annotations

import sys

from app.services.inference import provider, InferenceError
from app import config


def main() -> int:
    print(f"Base URL:        {config.INFERENCE_BASE_URL}")
    print(f"Primary model:   {config.PRIMARY_MODEL}")
    print(f"Allowed models:  {sorted(config.ALLOWED_MODELS)}")
    if not provider.configured:
        print("\n[SKIP] OPENROUTER_API_KEY not set. Open-weight call not attempted.")
        print("       Set the key (stand-in for the self-hosted vLLM key) and re-run to verify live.")
        return 0
    try:
        result = provider.complete(
            "Reply with exactly: INFERENCE OK",
            system="You are a terse test harness.",
            max_tokens=16,
        )
        print(f"\n[OK] Model {result.model} replied: {result.text!r}")
        return 0
    except InferenceError as exc:
        print(f"\n[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
