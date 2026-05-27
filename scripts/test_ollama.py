"""Smoke test for Ollama + instructor structured output.

Run from project root:
    uv run python scripts/test_ollama.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running this script directly from the scripts/ folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import instructor
from openai import OpenAI
from pydantic import BaseModel, Field

from src.config import settings


class ListingExtraction(BaseModel):
    """Structured fields we want to pull out of a raw marketplace listing."""

    brand: str = Field(description="Brand name of the product")
    product_type: str = Field(description="Category, e.g. 'shoes', 'jacket'")
    condition: str = Field(description="One of: new, like-new, used-good, used-fair, for-parts")
    size: str | None = Field(default=None, description="Size if applicable, else null")
    color: str | None = Field(default=None, description="Primary color if mentioned")
    estimated_retail_price_usd: float | None = Field(
        default=None,
        description="Rough estimate of original retail price in USD, null if uncertain",
    )


SAMPLE_LISTING = """
Nike Air Jordan 1 Retro High OG 'Chicago' 2022 — Men's Size 10.5.
Worn maybe 5 times, original box included. Red/white/black colorway.
No major scuffs, minor crease on toe box. Retail was $180.
"""


def main() -> None:
    print(f"Connecting to Ollama at {settings.ollama_base_url}")
    print(f"Model: {settings.ollama_model}")
    print("-" * 60)

    raw_client = OpenAI(
        base_url=settings.ollama_base_url,
        api_key=settings.ollama_api_key,
    )
    client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)

    result = client.chat.completions.create(
        model=settings.ollama_model,
        response_model=ListingExtraction,
        messages=[
            {
                "role": "system",
                "content": "You extract structured product information from marketplace listings. "
                "Return only valid JSON matching the schema.",
            },
            {"role": "user", "content": f"Listing:\n{SAMPLE_LISTING}"},
        ],
        max_retries=2,
    )

    print("Extracted fields:")
    for field, value in result.model_dump().items():
        print(f"  {field:30s} = {value!r}")
    print("-" * 60)
    print("OK — Ollama + instructor pipeline working.")


if __name__ == "__main__":
    main()
