"""Benchmark different models on a single complex parsing task.

Compares: qwen3:4b (thinking), qwen3:4b (/no_think), qwen2.5-coder:7b, gemma3:4b
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import instructor
from openai import OpenAI

from src.config import settings
from src.extractors.mock import MockExtractor
from src.parser.llm_parser import _SYSTEM_PROMPT, _build_user_prompt
from src.parser.schemas import ParsedListing


def bench(model: str, raw, *, no_think_directive: bool = False) -> dict:
    client_raw = OpenAI(base_url=settings.ollama_base_url, api_key=settings.ollama_api_key)
    client = instructor.from_openai(client_raw, mode=instructor.Mode.JSON)

    user_msg = _build_user_prompt(raw)
    if not no_think_directive and user_msg.startswith("/no_think\n\n"):
        user_msg = user_msg.removeprefix("/no_think\n\n")

    start = time.time()
    try:
        result = client.chat.completions.create(
            model=model,
            response_model=ParsedListing,
            max_retries=2,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            extra_body={"think": False} if no_think_directive else {},
        )
        elapsed = time.time() - start
        return {
            "model": model,
            "elapsed": elapsed,
            "ok": True,
            "brand": result.brand,
            "product_type": result.product_type,
            "condition": result.condition.value,
        }
    except Exception as exc:
        elapsed = time.time() - start
        return {"model": model, "elapsed": elapsed, "ok": False, "error": str(exc)[:100]}


def main() -> None:
    extractor = MockExtractor()
    # Pick the Rolex listing — it was the toughest one that failed last time.
    raw = extractor.get_item("mock-ebay-004")

    print(f"Benchmark prompt: {raw.title}")
    print("=" * 70)

    cases = [
        ("qwen3:4b", False, "qwen3:4b WITH thinking"),
        ("qwen3:4b", True, "qwen3:4b WITHOUT thinking (no_think + think:false)"),
        ("qwen2.5-coder:7b", True, "qwen2.5-coder:7b (non-thinking)"),
        ("gemma3:4b", True, "gemma3:4b (non-thinking)"),
    ]

    for model, no_think, label in cases:
        print(f"\n--- {label} ---")
        result = bench(model, raw, no_think_directive=no_think)
        if result["ok"]:
            print(f"  elapsed:      {result['elapsed']:.1f}s")
            print(f"  brand:        {result['brand']}")
            print(f"  product_type: {result['product_type']}")
            print(f"  condition:    {result['condition']}")
        else:
            print(f"  elapsed:      {result['elapsed']:.1f}s  (FAILED)")
            print(f"  error:        {result['error']}")


if __name__ == "__main__":
    main()
