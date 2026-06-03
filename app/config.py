"""Central config. Inference points at OpenRouter as a cost stand-in for self-hosted
vLLM (decision D-002) — swapping to sovereign infra is a base-URL + key change here,
with no code change anywhere else (Invariant 4 / VAL-GOV-002)."""
from __future__ import annotations

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
PERSONA_DIR = DATA_DIR / "personas"
DB_PATH = APP_DIR.parent / "foundry.db"  # gitignored runtime file

# --- Inference (OpenAI-compatible endpoint) ---
# To go sovereign: set OPENROUTER_BASE_URL to your vLLM server and swap the key. Nothing else changes.
INFERENCE_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
INFERENCE_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Open-weight models ONLY (Invariant 4). gpt-oss-120b is OpenAI's *open-weight* MoE
# (MXFP4, fits one 80GB H100) despite the vendor prefix in its OpenRouter id.
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "meta-llama/llama-3.3-70b-instruct"

# Hard allowlist enforced in inference.py. If a model isn't here, the call is refused.
# This is a code-level guarantee for VAL-GOV-002: no closed/proprietary model can enter the path.
ALLOWED_MODELS = frozenset({PRIMARY_MODEL, FALLBACK_MODEL})

# Single demo worker identity (no auth in scope — see missions.md out-of-scope).
DEMO_WORKER = "Sam Ellison (keyworker)"
