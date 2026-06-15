"""LLM market-insights generator.

Builds a compact, deterministic "market brief" from already-aggregated stats,
then asks a local LLM to reason over ONLY those facts. Grounding the model on
pre-computed aggregates (instead of raw rows) keeps insights faithful to the
data and cheap to run — the same governed-RAG principle, applied small.
"""
from __future__ import annotations

import pandas as pd
import instructor
from loguru import logger
from openai import OpenAI

from src.analytics.deal_score import top_opportunities
from src.analytics.queries import (
    brand_summary,
    condition_distribution,
    price_stats,
    quality_signals_summary,
    sell_through_rate,
)
from src.config import settings
from src.insights.schemas import MarketInsights

_SYSTEM_PROMPT = """You are a market analyst for an online reseller.

You are given a MARKET BRIEF of pre-aggregated statistics about a set of
marketplace listings. Produce concise, decision-useful insights.

Rules:
- Ground EVERY claim in the numbers provided. Never invent figures.
- Think like a reseller: where is the margin, what's in demand, what's risky.
- Be specific and quantitative ("Nike averages $X across N listings"), not vague.
- Return ONLY valid JSON matching the schema. No commentary, no reasoning text."""


def build_market_brief(df: pd.DataFrame, *, top_n: int = 8) -> str:
    """Render scored listings into a plain-text brief for the LLM."""
    stats = price_stats(df)
    lines: list[str] = [
        "== OVERVIEW ==",
        f"Listings: {stats['count']} | "
        f"price avg ${stats['mean']:,.0f}, median ${stats['median']:,.0f}, "
        f"range ${stats['min']:,.0f}-${stats['max']:,.0f} | "
        f"total inventory value ${stats['total']:,.0f}",
        "",
        "== BY BRAND (count, avg, median, total value) ==",
    ]
    for _, r in brand_summary(df).head(10).iterrows():
        lines.append(
            f"- {r['brand']}: {int(r['count'])} listings, "
            f"avg ${r['avg_price']:,.0f}, median ${r['median_price']:,.0f}, "
            f"total ${r['total_value']:,.0f}"
        )

    lines += ["", "== CONDITION MIX =="]
    for _, r in condition_distribution(df).iterrows():
        lines.append(f"- {r['condition']}: {int(r['count'])}")

    lines += ["", "== QUALITY / TRUST SIGNALS =="]
    for _, r in quality_signals_summary(df).iterrows():
        label = r["signal"].replace("has_", "").replace("_", " ")
        lines.append(f"- {label}: {int(r['count'])} / {len(df)}")

    if "status" in df.columns and df["status"].fillna("").eq("sold").any():
        lines += ["", "== SELL-THROUGH RATE BY BRAND (sold / total) =="]
        for _, r in sell_through_rate(df, by="brand").iterrows():
            if r["total"]:
                lines.append(
                    f"- {r['brand']}: {r['sell_through_pct']:.0f}% "
                    f"({int(r['sold'])}/{int(r['total'])} sold)"
                )

    # Profit potential only applies to listings you can still buy.
    active = df[df["status"].fillna("active").eq("active")] if "status" in df.columns else df
    lines += ["", f"== TOP {top_n} RESALE OPPORTUNITIES (active, by deal score) =="]
    for _, r in top_opportunities(active, n=top_n).iterrows():
        profit = ""
        if "est_net_profit_usd" in r and pd.notna(r["est_net_profit_usd"]):
            profit = (
                f", est. net ${r['est_net_profit_usd']:,.0f} "
                f"({r['est_roi_pct'] * 100:+.0f}% ROI)"
            )
        lines.append(
            f"- [{r['deal_score']}] {str(r['title'])[:65]} — "
            f"${r['price_value']:,.0f}{profit} ({r['deal_reason']})"
        )

    return "\n".join(lines)


class InsightGenerator:
    """Generates a structured MarketInsights report from a scored DataFrame."""

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

    def generate(self, df: pd.DataFrame) -> MarketInsights:
        """Build the brief and return structured market insights."""
        brief = build_market_brief(df)
        logger.info("Generating market insights over {} listings", len(df))
        return self._client.chat.completions.create(
            model=self.model,
            response_model=MarketInsights,
            max_retries=self.max_retries,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"/no_think\n\nMARKET BRIEF:\n{brief}"},
            ],
            # Ollama-native: disable reasoning for thinking-capable models.
            extra_body={"think": False},
        )
