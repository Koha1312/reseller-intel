"""Deal scoring: rank listings by resale opportunity (0-100).

Pure, deterministic, explainable — no LLM involved. The AI layer in
`src.insights` reasons over the *aggregates* this module produces, not raw rows.

The score answers a reseller's core question: "is this listing a good flip?"
A high score means priced below comparable listings, in good condition, with
trust/quality signals, and showing buyer demand.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Component weights (must sum to 1.0).
W_VALUE = 0.40  # priced below the comparable median = the biggest signal
W_CONDITION = 0.20
W_QUALITY = 0.20
W_DEMAND = 0.20

# Condition desirability for resale (0..1).
_CONDITION_SCORE = {
    "new": 1.0,
    "like-new": 0.85,
    "used-good": 0.60,
    "used-fair": 0.30,
    "for-parts": 0.10,
    "unknown": 0.40,
}

# Trust/quality signal contributions — already sum to 1.0 when all present.
_QUALITY_WEIGHTS = {
    "has_authenticity_proof": 0.40,
    "has_original_box": 0.30,
    "has_tags": 0.20,
    "is_vintage": 0.10,
}

# A confident value judgement needs at least this many real comparables.
MIN_PEERS = 3
# When falling back to a product_type peer set, ignore items priced more than
# this multiple above/below the type median (drops cross-tier outliers, e.g. a
# $12,500 Rolex distorting the "watches" median for an $85 Casio).
PRICE_BAND = 4.0

# Columns this module appends to the DataFrame.
SCORE_COLUMNS = [
    "ref_price",
    "n_comparables",
    "value_confident",
    "value_gap_pct",
    "score_value",
    "score_condition",
    "score_quality",
    "sell_through",
    "score_demand",
    "deal_score",
    "deal_reason",
]


def _resolve_references(df: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Resolve each listing's reference price, peer count, and confidence.

    A reference is only "confident" when backed by >= MIN_PEERS real comparables:
      1. same (brand, product_type) group, if it has enough peers; else
      2. same product_type, restricted to a price band around the type median
         (so different price tiers don't get mixed); else
      3. unresolved — the listing has too few comparables to judge value fairly.
    """
    ref = pd.Series(np.nan, index=df.index, dtype="float64")
    count = pd.Series(0, index=df.index, dtype="int64")

    # 1. Brand + product_type peers.
    bt_median = df.groupby(["brand", "product_type"])["price_value"].transform("median")
    bt_size = df.groupby(["brand", "product_type"])["price_value"].transform("size")
    use_bt = bt_size >= MIN_PEERS
    ref = ref.mask(use_bt, bt_median)
    count = count.mask(use_bt, bt_size.fillna(0).astype("int64"))

    # 2. Fallback: product_type peers within a sane price band around the type median.
    type_median = df.groupby("product_type")["price_value"].transform("median")
    in_band = df["price_value"].between(type_median / PRICE_BAND, type_median * PRICE_BAND)
    banded = df[in_band].groupby("product_type")["price_value"]
    band_median = df["product_type"].map(banded.median())
    band_size = df["product_type"].map(banded.size()).fillna(0).astype("int64")

    use_type = ref.isna() & (band_size >= MIN_PEERS)
    ref = ref.mask(use_type, band_median)
    count = count.mask(use_type, band_size)

    confident = ref.notna()
    return ref, count, confident


def _engagement_scores(df: pd.DataFrame) -> pd.Series:
    """Percentile-rank listings by engagement (watches weighted over views)."""
    raw = df["watch_count"].fillna(0) + 0.1 * df["view_count"].fillna(0)
    if raw.nunique() <= 1:
        # No usable engagement data — treat demand as neutral for everyone.
        return pd.Series(0.5, index=df.index)
    return raw.rank(pct=True)


def _sell_through(df: pd.DataFrame) -> pd.Series:
    """Per-listing sell-through rate of its (brand, product_type) peer group.

    Returns NaN for every row when there is no status data to compute from.
    """
    if "status" not in df.columns:
        return pd.Series(np.nan, index=df.index)
    is_sold = df["status"].fillna("").eq("sold")
    sold = is_sold.groupby([df["brand"], df["product_type"]]).transform("sum")
    total = df.groupby(["brand", "product_type"])["price_value"].transform("size")
    return (sold / total).where(total > 0)


def _demand_scores(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Demand score (0..1) plus the raw sell-through series.

    Demand blends engagement (how many people are watching) with sell-through
    (how reliably the segment actually sells). Sell-through is only mixed in when
    the dataset has real sold data; otherwise demand is pure engagement.
    """
    engagement = _engagement_scores(df)
    str_series = _sell_through(df)

    has_sales = (
        "status" in df.columns
        and df["status"].fillna("").eq("sold").any()
        and str_series.notna().any()
    )
    if has_sales:
        demand = 0.5 * engagement + 0.5 * str_series.fillna(0.0)
    else:
        demand = engagement
    return demand, str_series


def _deal_reason(row: pd.Series) -> str:
    """One short human-readable explanation of the dominant positive factor."""
    bits: list[str] = []
    gap = row["value_gap_pct"]
    n = int(row["n_comparables"])
    if row["value_confident"] and pd.notna(gap) and gap >= 0.10:
        bits.append(f"~{gap * 100:.0f}% below median ({n} comps)")
    elif row["value_confident"] and pd.notna(gap) and gap <= -0.10:
        bits.append(f"~{abs(gap) * 100:.0f}% above median ({n} comps)")

    if row["condition"] in ("new", "like-new"):
        bits.append(str(row["condition"]))
    if row.get("has_authenticity_proof"):
        bits.append("authenticated")
    if row.get("has_original_box"):
        bits.append("orig. box")
    str_ = row.get("sell_through")
    if pd.notna(str_) and str_ >= 0.5:
        bits.append(f"fast mover ({str_ * 100:.0f}% STR)")
    elif row["score_demand"] >= 0.75:
        bits.append("high demand")

    if bits:
        return " · ".join(bits)
    # Nothing notable to say — be honest about why rather than implying a deal.
    return "limited comparables — priced as-is" if not row["value_confident"] else "priced near market"


def compute_deal_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with deal-score columns appended (see SCORE_COLUMNS).

    Scores must be computed on the FULL dataset (peer medians and demand ranks
    are dataset-relative), then filtered downstream — never the reverse.
    """
    if df.empty:
        return df.assign(**{col: pd.Series(dtype="float64") for col in SCORE_COLUMNS})

    out = df.copy()

    # 1. Value: how far below the peer-group median this listing is priced.
    #    Only judged when there are enough real comparables; otherwise neutral.
    ref, count, confident = _resolve_references(out)
    out["ref_price"] = ref
    out["n_comparables"] = count
    out["value_confident"] = confident
    out["value_gap_pct"] = ((ref - out["price_value"]) / ref).where(confident)
    # 0% gap -> 0.5 (neutral); -50% (cheaper) -> ~1.0; +50% (pricier) -> ~0.0.
    # Listings without enough comparables stay neutral (0.5) — we don't guess.
    out["score_value"] = (0.5 + out["value_gap_pct"]).clip(0.0, 1.0).fillna(0.5)

    # 2. Condition desirability.
    out["score_condition"] = out["condition"].map(_CONDITION_SCORE).fillna(0.40)

    # 3. Quality / trust signals.
    quality = pd.Series(0.0, index=out.index)
    for col, weight in _QUALITY_WEIGHTS.items():
        if col in out.columns:
            quality += out[col].fillna(False).astype(float) * weight
    out["score_quality"] = quality.clip(0.0, 1.0)

    # 4. Buyer demand — engagement blended with sell-through where available.
    demand, sell_through = _demand_scores(out)
    out["sell_through"] = sell_through
    out["score_demand"] = demand

    # Weighted blend -> 0..100.
    out["deal_score"] = (
        100.0
        * (
            W_VALUE * out["score_value"]
            + W_CONDITION * out["score_condition"]
            + W_QUALITY * out["score_quality"]
            + W_DEMAND * out["score_demand"]
        )
    ).round().astype(int)

    out["deal_reason"] = out.apply(_deal_reason, axis=1)
    return out


def top_opportunities(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Highest-scoring listings, assuming `df` already has deal_score columns."""
    if df.empty or "deal_score" not in df.columns:
        return df
    return df.sort_values("deal_score", ascending=False).head(n)
