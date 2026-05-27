"""Debug: which method actually disables qwen3 thinking mode?

Compares 4 approaches and reports timing + token count for each.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from src.config import settings

PROMPT = "What is 2+2? Answer with only a single number, no explanation."


def run(label: str, messages: list[dict], extra: dict | None = None) -> None:
    client = OpenAI(base_url=settings.ollama_base_url, api_key=settings.ollama_api_key)
    start = time.time()
    kwargs: dict = {"model": settings.ollama_model, "messages": messages}
    if extra:
        kwargs["extra_body"] = extra
    resp = client.chat.completions.create(**kwargs)
    elapsed = time.time() - start

    msg = resp.choices[0].message
    content = msg.content or ""
    reasoning = getattr(msg, "reasoning", None) or ""
    usage = resp.usage

    print(f"\n--- {label} ---")
    print(f"  elapsed:        {elapsed:.2f}s")
    print(f"  total tokens:   {usage.total_tokens}")
    print(f"  content (len {len(content)}):  {content[:100]!r}")
    print(f"  reasoning len:  {len(reasoning)} chars")


def main() -> None:
    print(f"Model: {settings.ollama_model}")
    print("=" * 60)

    run(
        "A. baseline (thinking on, no override)",
        [{"role": "user", "content": PROMPT}],
    )

    run(
        "B. /no_think in SYSTEM prompt",
        [
            {"role": "system", "content": "/no_think\nAnswer concisely."},
            {"role": "user", "content": PROMPT},
        ],
    )

    run(
        "C. /no_think in USER message",
        [{"role": "user", "content": f"/no_think\n{PROMPT}"}],
    )

    run(
        "D. extra_body think:false",
        [{"role": "user", "content": PROMPT}],
        extra={"think": False},
    )

    run(
        "E. extra_body reasoning.effort:'none'",
        [{"role": "user", "content": PROMPT}],
        extra={"reasoning": {"effort": "none"}},
    )

    run(
        "F. extra_body reasoning.effort:'low'",
        [{"role": "user", "content": PROMPT}],
        extra={"reasoning": {"effort": "low"}},
    )


if __name__ == "__main__":
    main()
