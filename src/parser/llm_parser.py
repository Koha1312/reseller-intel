"""LLM-powered parser: RawListing -> ParsedListing.

Uses instructor + Ollama (OpenAI-compatible endpoint) to extract structured
fields from raw marketplace text. Default model: qwen3:4b running locally.
"""
from __future__ import annotations

from datetime import datetime, timezone

import instructor
from loguru import logger
from openai import OpenAI

from src.config import settings
from src.parser.schemas import EnrichedListing, ParsedListing, RawListing

_SYSTEM_PROMPT = """You extract structured product information from online marketplace listings.

Rules:
- Return ONLY valid JSON matching the requested schema. No reasoning, no commentary.
- If a field is not present or unclear, return null (or false for booleans).
- Use EXACT brand names from the listing text. Do not substitute, translate, or "correct" brand names.
- Normalize the condition to one of: new, like-new, used-good, used-fair, for-parts, unknown.
- "NWT", "deadstock", "brand new", "new with tags/box" -> "new".
- "Like new", "worn once", "barely worn", "DS-ish" -> "like-new".
- "Pre-owned" with light wear -> "used-good".
- Heavy wear, beaters, "honest wear" with sole/edge damage -> "used-fair".
- Damaged, parts-only -> "for-parts".
- ALWAYS extract brand if present. Brand is the maker — usually the FIRST capitalized word or known company name in the title (e.g. Nike, adidas, Supreme, Coach, Hermes, Rolex, Louis Vuitton, Levi's, Casio). Return null only if no brand at all is identifiable.
- Model is the product line, NOT including the brand (Air Jordan 1, Speedy 25, Submariner, Box Logo Hoodie).
- Set has_original_box / has_tags / has_authenticity_proof / is_vintage ONLY when explicitly mentioned.
- key_features: up to 5 short notable phrases. Skip if nothing notable."""


def _build_user_prompt(raw: RawListing) -> str:
    # `/no_think` directive disables qwen3's reasoning mode (~2x faster, more reliable JSON).
    parts = ["/no_think", f"Title: {raw.title}", f"Platform condition label: {raw.condition_raw}"]
    if raw.description:
        parts.append(f"Description:\n{raw.description}")
    if raw.category_name:
        parts.append(f"Category: {raw.category_name}")
    return "\n\n".join(parts)


class ListingParser:
    """Parses raw listings into structured ParsedListing records via local LLM."""

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        max_retries: int = 2,
    ) -> None:
        self.model = model or settings.ollama_model
        self.base_url = base_url or settings.ollama_base_url
        self.api_key = api_key or settings.ollama_api_key
        self.max_retries = max_retries

        raw_client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self._client = instructor.from_openai(raw_client, mode=instructor.Mode.JSON)

    def parse(self, raw: RawListing) -> ParsedListing:
        """Parse one listing. Raises on persistent failure."""
        return self._client.chat.completions.create(
            model=self.model,
            response_model=ParsedListing,
            max_retries=self.max_retries,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(raw)},
            ],
            # Ollama-native: disable reasoning for thinking-capable models (qwen3, etc.)
            extra_body={"think": False},
        )

    def parse_many(
        self,
        raws: list[RawListing],
        *,
        skip_errors: bool = True,
    ) -> list[EnrichedListing]:
        """Parse a batch of raw listings. Logs progress; optionally skips failures."""
        results: list[EnrichedListing] = []
        total = len(raws)

        for idx, raw in enumerate(raws, start=1):
            logger.info("Parsing {}/{}: {}", idx, total, raw.title[:60])
            try:
                parsed = self.parse(raw)
                results.append(
                    EnrichedListing(
                        raw=raw,
                        parsed=parsed,
                        parsed_at=datetime.now(timezone.utc),
                        parser_model=self.model,
                    )
                )
            except Exception as exc:
                logger.error("Parse failed for {}: {}", raw.listing_id, exc)
                if not skip_errors:
                    raise
                results.append(
                    EnrichedListing(
                        raw=raw,
                        parsed=None,
                        parsed_at=None,
                        parser_model=self.model,
                    )
                )

        return results
