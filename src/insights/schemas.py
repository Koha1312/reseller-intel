"""Pydantic schemas for LLM-generated market insights."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class InsightCategory(str, Enum):
    PRICING = "pricing"
    OPPORTUNITY = "opportunity"
    DEMAND = "demand"
    RISK = "risk"
    TREND = "trend"


class MarketInsight(BaseModel):
    """A single, data-grounded finding about the current listing set."""

    headline: str = Field(description="Punchy one-line finding (max ~12 words).")
    detail: str = Field(
        description="1-2 sentences explaining the finding, citing concrete numbers "
        "from the brief. Never invent figures not present in the data."
    )
    category: InsightCategory = Field(
        description="pricing | opportunity | demand | risk | trend."
    )


class MarketInsights(BaseModel):
    """Structured market-intelligence report over a set of listings."""

    summary: str = Field(
        description="One-paragraph executive summary for a reseller (2-4 sentences)."
    )
    insights: list[MarketInsight] = Field(
        description="3-6 distinct, non-overlapping insights ordered by usefulness.",
    )
