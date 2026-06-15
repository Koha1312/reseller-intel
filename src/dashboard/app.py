"""Streamlit dashboard for Reseller Intel.

Launch from project root:
    uv run streamlit run src/dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `src` importable when Streamlit launches this file directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.analytics.deal_score import compute_deal_scores, top_opportunities
from src.analytics.profit import (
    DEFAULT_FEE_PCT,
    DEFAULT_SHIPPING_USD,
    estimate_profit,
)
from src.analytics.queries import (
    brand_summary,
    condition_distribution,
    load_listings_df,
    price_stats,
    product_type_distribution,
    quality_signals_summary,
    sell_through_rate,
)
from src.dashboard.theme import inject_global_css, render_hero


st.set_page_config(
    page_title="Reseller Intel",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=60)
def get_data() -> pd.DataFrame:
    # Deal scores are dataset-relative, so compute on the FULL set before filtering.
    # Profit uses ref_price from scoring, so it must run after compute_deal_scores.
    return estimate_profit(compute_deal_scores(load_listings_df()))


def main() -> None:
    inject_global_css()
    render_hero()

    df = get_data()

    st.caption(
        "Marketplace listing intelligence — extract, enrich, and analyze reselling data across platforms."
    )

    if df.empty:
        st.warning("No listings in database yet. Run `uv run python scripts/seed.py` to populate.")
        return

    _render_sidebar_filters(df)
    filtered = _apply_filters(df)

    _render_metrics(filtered)
    st.divider()

    _render_charts(filtered)
    st.divider()

    _render_opportunities(filtered)
    st.divider()

    col_str, col_profit = st.columns(2)
    with col_str:
        _render_sell_through(filtered)
    with col_profit:
        _render_profit_estimator(filtered)
    st.divider()

    _render_insights(filtered)
    st.divider()

    _render_table(filtered)


def _render_sidebar_filters(df: pd.DataFrame) -> None:
    st.sidebar.header("Filters")

    brands = sorted([b for b in df["brand"].dropna().unique()])
    selected_brands = st.sidebar.multiselect("Brand", brands, default=[])

    conditions = sorted([c for c in df["condition"].dropna().unique()])
    selected_conditions = st.sidebar.multiselect("Condition", conditions, default=[])

    types = sorted([t for t in df["product_type"].dropna().unique()])
    selected_types = st.sidebar.multiselect("Product type", types, default=[])

    price_min = float(df["price_value"].min())
    price_max = float(df["price_value"].max())
    price_range = st.sidebar.slider(
        "Price (USD)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max),
        step=10.0,
    )

    quality_only = st.sidebar.checkbox("Only items with authenticity proof", value=False)
    box_only = st.sidebar.checkbox("Only items with original box", value=False)

    st.sidebar.caption(f"Total listings in DB: **{len(df)}**")

    st.session_state["filter_brands"] = selected_brands
    st.session_state["filter_conditions"] = selected_conditions
    st.session_state["filter_types"] = selected_types
    st.session_state["filter_price_range"] = price_range
    st.session_state["filter_quality_only"] = quality_only
    st.session_state["filter_box_only"] = box_only


def _apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filtered = df.copy()

    if brands := st.session_state.get("filter_brands"):
        filtered = filtered[filtered["brand"].isin(brands)]

    if conditions := st.session_state.get("filter_conditions"):
        filtered = filtered[filtered["condition"].isin(conditions)]

    if types := st.session_state.get("filter_types"):
        filtered = filtered[filtered["product_type"].isin(types)]

    if price_range := st.session_state.get("filter_price_range"):
        low, high = price_range
        filtered = filtered[(filtered["price_value"] >= low) & (filtered["price_value"] <= high)]

    if st.session_state.get("filter_quality_only"):
        filtered = filtered[filtered["has_authenticity_proof"].fillna(False)]

    if st.session_state.get("filter_box_only"):
        filtered = filtered[filtered["has_original_box"].fillna(False)]

    return filtered


def _render_metrics(df: pd.DataFrame) -> None:
    stats = price_stats(df)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Listings", stats["count"])
    col2.metric("Avg price", f"${stats['mean']:,.0f}")
    col3.metric("Median price", f"${stats['median']:,.0f}")
    col4.metric("Total value", f"${stats['total']:,.0f}")
    col5.metric("Unique brands", df["brand"].nunique())
    avg_deal = df["deal_score"].mean() if "deal_score" in df.columns and not df.empty else 0
    col6.metric("Avg deal score", f"{avg_deal:.0f}/100")


def _render_charts(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("No listings match the current filters.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Listings by brand")
        b_summary = brand_summary(df)
        fig = px.bar(
            b_summary,
            x="brand",
            y="count",
            color="avg_price",
            color_continuous_scale="Viridis",
            labels={"count": "Listings", "avg_price": "Avg price (USD)"},
        )
        fig.update_layout(height=380, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Condition mix")
        c_dist = condition_distribution(df)
        fig = px.pie(c_dist, values="count", names="condition", hole=0.45)
        fig.update_layout(height=380, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Price distribution by brand")
        fig = px.box(
            df,
            x="brand",
            y="price_value",
            points="all",
            log_y=True,
            labels={"price_value": "Price (USD, log scale)"},
        )
        fig.update_layout(height=400, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Engagement vs price")
        plot_df = df.copy()
        plot_df["watch_count"] = plot_df["watch_count"].fillna(0)
        plot_df["view_count"] = plot_df["view_count"].fillna(0)
        fig = px.scatter(
            plot_df,
            x="price_value",
            y="watch_count",
            color="brand",
            size="view_count",
            hover_data=["title"],
            log_x=True,
            labels={"price_value": "Price (USD)", "watch_count": "Watches"},
        )
        fig.update_layout(height=400, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Product type breakdown")
    col5, col6 = st.columns([2, 1])

    with col5:
        type_dist = product_type_distribution(df)
        fig = px.bar(type_dist, x="product_type", y="count")
        fig.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        st.markdown("**Quality signals**")
        signals = quality_signals_summary(df)
        for _, row in signals.iterrows():
            label = row["signal"].replace("_", " ").replace("has ", "").title()
            pct = row["count"] / len(df) * 100 if len(df) > 0 else 0
            st.metric(label, f"{row['count']} / {len(df)}", delta=f"{pct:.0f}%")


def _render_opportunities(df: pd.DataFrame) -> None:
    st.subheader("🔥 Top resale opportunities")
    st.caption(
        "Active listings ranked by deal score (0–100): priced below comparable "
        "listings, good condition, trust signals, demand & sell-through. "
        "Profit = resell at market target minus fees & shipping."
    )
    # You can only buy what's still active — sold rows feed the stats, not the buy list.
    active = df[df["status"].fillna("active").eq("active")] if "status" in df.columns else df
    if active.empty:
        st.info("No active listings match the current filters.")
        return

    top = top_opportunities(active, n=10)
    table = top[["deal_score", "title", "brand", "price_value", "ref_price",
                 "value_gap_pct", "est_net_profit_usd", "est_roi_pct", "sell_through",
                 "deal_reason", "item_url"]].rename(columns={
        "deal_score": "Score",
        "title": "Title",
        "brand": "Brand",
        "price_value": "Price",
        "ref_price": "Market",
        "value_gap_pct": "Gap",
        "est_net_profit_usd": "Net profit",
        "est_roi_pct": "ROI",
        "sell_through": "STR",
        "deal_reason": "Why",
        "item_url": "URL",
    })
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=100, format="%d"
            ),
            "Price": st.column_config.NumberColumn("Price", format="$%.0f"),
            "Market": st.column_config.NumberColumn("Market", format="$%.0f"),
            "Gap": st.column_config.NumberColumn("Gap", format="%+.0f%%"),
            "Net profit": st.column_config.NumberColumn("Net profit", format="$%.0f"),
            "ROI": st.column_config.NumberColumn("ROI", format="%+.0f%%"),
            "STR": st.column_config.NumberColumn(
                "STR", format="%.0f%%", help="Sell-through rate of this brand+type segment."
            ),
            "URL": st.column_config.LinkColumn("URL", display_text="↗"),
        },
    )


def _render_sell_through(df: pd.DataFrame) -> None:
    st.subheader("📉 Sell-through rate by brand")
    st.caption("Sold ÷ total listings — how reliably each brand actually moves.")
    if df.empty or "status" not in df.columns:
        st.info("No status data available.")
        return

    str_df = sell_through_rate(df, by="brand")
    str_df = str_df[str_df["total"] > 0]
    if str_df.empty or str_df["sold"].sum() == 0:
        st.info("No sold listings yet — re-seed with sold comps to populate this.")
        return

    fig = px.bar(
        str_df, x="brand", y="sell_through_pct",
        color="sell_through_pct", color_continuous_scale="Tealgrn",
        labels={"sell_through_pct": "Sell-through %", "brand": "Brand"},
        hover_data=["sold", "total"],
    )
    fig.update_layout(height=340, margin=dict(t=30, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_profit_estimator(df: pd.DataFrame) -> None:
    st.subheader("💵 Profit estimator")
    st.caption("Tune marketplace fee & shipping to see take-home on the active list.")
    active = df[df["status"].fillna("active").eq("active")] if "status" in df.columns else df
    if active.empty:
        st.info("No active listings match the current filters.")
        return

    col1, col2 = st.columns(2)
    fee = col1.slider("Marketplace fee %", 0.0, 30.0, DEFAULT_FEE_PCT * 100, step=0.25) / 100
    shipping = col2.slider("Shipping $", 0.0, 50.0, DEFAULT_SHIPPING_USD, step=1.0)

    recomputed = estimate_profit(active, fee_pct=fee, shipping_usd=shipping)
    total_net = recomputed["est_net_profit_usd"].clip(lower=0).sum()
    avg_roi = recomputed["est_roi_pct"].mean() * 100
    profitable = int((recomputed["est_net_profit_usd"] > 0).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Profitable flips", f"{profitable} / {len(recomputed)}")
    m2.metric("Avg ROI", f"{avg_roi:+.0f}%")
    m3.metric("Total upside", f"${total_net:,.0f}")


def _render_insights(df: pd.DataFrame) -> None:
    st.subheader("💡 AI market insights")
    st.caption(
        "LLM-generated analysis grounded in the aggregates above. "
        "Runs on a local model (Ollama) — works on your machine; in the hosted "
        "demo everything else works, this one needs your local LLM."
    )

    if df.empty:
        st.info("No listings match the current filters.")
        return

    if st.button("✨ Generate insights", type="primary"):
        try:
            # Imported lazily so the dashboard still loads without the LLM stack.
            from src.insights.generator import InsightGenerator

            with st.spinner("Analyzing the market…"):
                report = InsightGenerator().generate(df)
            st.session_state["insights_report"] = report
        except Exception:  # noqa: BLE001 — no local LLM (e.g. hosted demo): degrade gracefully
            st.info(
                "✨ AI insights run locally via Ollama. The charts, deal scores, "
                "sell-through and profit estimates all work everywhere — run the "
                "app on your machine with Ollama to generate the written analysis."
            )
            return

    report = st.session_state.get("insights_report")
    if report is None:
        return

    st.markdown(f"**Executive summary** — {report.summary}")
    for ins in report.insights:
        with st.container(border=True):
            st.markdown(f"**{ins.headline}**  &nbsp; `{ins.category.value}`")
            st.write(ins.detail)


def _render_table(df: pd.DataFrame) -> None:
    st.subheader(f"Listings ({len(df)})")

    display_cols = [
        "deal_score",
        "title",
        "brand",
        "model_name",
        "condition",
        "size",
        "price_value",
        "price_currency",
        "watch_count",
        "view_count",
        "seller_username",
        "item_url",
    ]
    table_df = df[display_cols].copy()
    table_df = table_df.rename(columns={
        "deal_score": "Score",
        "price_value": "Price",
        "price_currency": "Cur",
        "watch_count": "Watches",
        "view_count": "Views",
        "seller_username": "Seller",
        "item_url": "URL",
    })

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Score", min_value=0, max_value=100, format="%d"
            ),
            "URL": st.column_config.LinkColumn("URL", display_text="↗"),
            "Price": st.column_config.NumberColumn("Price", format="$%.0f"),
        },
    )


if __name__ == "__main__":
    main()
