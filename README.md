# 📊 Reseller Intel

Marketplace listing intelligence for online resellers — **extract** listings,
**enrich** them with an LLM, and surface the numbers that actually drive a flip:
opportunity scores, sell-through rate, and profit-after-fees.

Built as a clean, layered pipeline so swapping the data source (eBay, Poshmark,
…) only touches the extraction layer.

## ✨ Features

- **🔥 Deal score (0–100)** — an explainable resale-opportunity score blending
  price-vs-comparables, condition, trust signals, demand and sell-through.
  Only judges value when there are enough real comparables (no fake discounts).
- **📉 Sell-through rate** — the reseller's #1 metric: how reliably each segment
  actually sells (sold ÷ total).
- **💵 Profit estimator** — take-home after marketplace fees + shipping, with
  interactive fee/shipping sliders and ROI.
- **🧠 AI market insights** — a local LLM (Ollama) reasons over the aggregates
  to write a short, grounded market brief.
- **🎬 3D dashboard** — an animated Streamlit UI with a 3D hero and tasteful motion.

## 🏗️ Architecture

```
Extraction (per-platform)  →  AI parsing (LLM)  →  Storage (SQLite)
        →  Analytics (deal score · sell-through · profit)  →  Dashboard (Streamlit)
```

Each layer is independent — swapping marketplace = swap the extraction module only.

## 🛠️ Tech

Python 3.12 · Streamlit · Plotly · pandas · SQLAlchemy · Pydantic ·
instructor + Ollama (local LLM) · uv

## 🚀 Run locally

```bash
uv sync
uv run python scripts/seed.py          # seed demo data (needs Ollama for parsing)
uv run streamlit run src/dashboard/app.py
```

> The repo ships with a pre-seeded `data/reseller.db` so the dashboard works
> out of the box. The **AI insights** button needs a local Ollama model
> (`OLLAMA_MODEL`, default `qwen2.5-coder:7b`); everything else works without it.

## 🧪 Tests

```bash
uv run --with pytest pytest -q
```

## ☁️ Deploy

Entry point `streamlit_app.py` is auto-detected by **Streamlit Community Cloud**
and **Hugging Face Spaces**. The hosted demo runs the full dashboard from the
bundled SQLite data; the AI-insights button is local-only (shows a friendly note
in the cloud).

---

*Demo uses mock eBay-shaped data. No real marketplace credentials or API keys are
required or stored.*

---

<p align="center"><sub>Built by <b>Khoa Nguyen</b>, paired with Claude 💙</sub></p>
