"""Visual theme: a 3D first-impression hero + tasteful motion throughout.

Everything here is pure CSS/JS injected into Streamlit — no extra dependencies,
no network calls. The goal is "wow on first use" without hurting daily usability:
one rich 3D moment at the top, subtle entrance + hover motion everywhere else.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

# Brand palette (kept in sync with the hero scene below).
_ACCENT = "#7c5cff"
_ACCENT_2 = "#22d3ee"


def inject_global_css() -> None:
    """Inject keyframes + subtle motion/3D polish onto Streamlit's own elements."""
    st.markdown(
        f"""
        <style>
        /* ---------- keyframes ---------- */
        @keyframes ri-rise {{
            from {{ opacity: 0; transform: translate3d(0, 18px, 0); }}
            to   {{ opacity: 1; transform: translate3d(0, 0, 0); }}
        }}
        @keyframes ri-gradient {{
            0%   {{ background-position: 0% 50%; }}
            100% {{ background-position: 200% 50%; }}
        }}
        @keyframes ri-shimmer {{
            0%   {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}

        /* ---------- section entrance ---------- */
        [data-testid="stVerticalBlock"] > div:has(> [data-testid="stHeading"]),
        [data-testid="stMetric"],
        [data-testid="stDataFrame"] {{
            animation: ri-rise 0.6s cubic-bezier(.21,.61,.35,1) both;
        }}

        /* ---------- animated gradient headings ---------- */
        [data-testid="stHeading"] h1,
        [data-testid="stHeading"] h2,
        [data-testid="stHeading"] h3 {{
            background: linear-gradient(100deg, #e8e6ff, {_ACCENT_2}, {_ACCENT}, #e8e6ff);
            background-size: 200% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: ri-gradient 6s linear infinite;
        }}

        /* ---------- 3D tilt + lift on metric cards ---------- */
        [data-testid="stMetric"] {{
            background: linear-gradient(160deg, rgba(124,92,255,.10), rgba(34,211,238,.05));
            border: 1px solid rgba(124,92,255,.22);
            border-radius: 14px;
            padding: 14px 16px;
            transform-style: preserve-3d;
            transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease;
            will-change: transform;
        }}
        [data-testid="stMetric"]:hover {{
            transform: perspective(700px) rotateX(6deg) rotateY(-6deg) translateY(-6px);
            box-shadow: 0 18px 40px -18px rgba(124,92,255,.65);
            border-color: rgba(34,211,238,.55);
        }}

        /* ---------- buttons: gradient + shimmer ---------- */
        [data-testid="stButton"] button[kind="primary"] {{
            background: linear-gradient(110deg, {_ACCENT}, {_ACCENT_2});
            background-size: 200% auto;
            border: 0;
            transition: transform .2s ease, box-shadow .2s ease, background-position .6s ease;
        }}
        [data-testid="stButton"] button[kind="primary"]:hover {{
            background-position: right center;
            transform: translateY(-2px);
            box-shadow: 0 12px 26px -10px rgba(34,211,238,.7);
        }}

        /* ---------- dataframe hover lift ---------- */
        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            transition: transform .25s ease, box-shadow .25s ease;
        }}
        [data-testid="stDataFrame"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 16px 34px -20px rgba(34,211,238,.5);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Self-contained 3D scene (CSS 3D transforms + a touch of JS for mouse parallax).
_HERO_HTML = f"""
<div id="ri-hero">
  <div class="ri-bg"></div>
  <div class="ri-stage">
    <div class="ri-card c1"><span class="ico">👟</span><span class="tag">+106%</span></div>
    <div class="ri-card c2"><span class="ico">👜</span><span class="tag">A+</span></div>
    <div class="ri-card c3"><span class="ico">⌚</span><span class="tag">50% STR</span></div>
    <div class="ri-card c4"><span class="ico">🧢</span><span class="tag">NWT</span></div>
  </div>
  <div class="ri-copy">
    <h1>Reseller&nbsp;Intel</h1>
    <p>Spot the flip. Know the margin. Move first.</p>
  </div>
</div>
<style>
  #ri-hero {{
    position: relative; height: 240px; border-radius: 18px; overflow: hidden;
    font-family: "Source Sans Pro", system-ui, sans-serif;
    perspective: 900px;
  }}
  .ri-bg {{
    position: absolute; inset: 0;
    background: linear-gradient(120deg, #120f2e, #1b1147 35%, #0c2540 70%, #102a3a);
    background-size: 300% 300%;
    animation: ri-bgshift 14s ease infinite;
  }}
  .ri-bg::after {{
    content: ""; position: absolute; inset: -40%;
    background: radial-gradient(closest-side, rgba(124,92,255,.35), transparent 70%),
                radial-gradient(closest-side, rgba(34,211,238,.30), transparent 70%);
    background-position: 25% 30%, 75% 70%;
    background-repeat: no-repeat;
    animation: ri-blob 12s ease-in-out infinite alternate;
  }}
  @keyframes ri-bgshift {{ 0%,100% {{ background-position: 0% 50%; }} 50% {{ background-position: 100% 50%; }} }}
  @keyframes ri-blob {{ from {{ transform: translate3d(-4%, -3%, 0) scale(1); }} to {{ transform: translate3d(5%, 4%, 0) scale(1.15); }} }}

  .ri-stage {{
    position: absolute; right: 6%; top: 50%; width: 46%; height: 100%;
    transform: translateY(-50%); transform-style: preserve-3d;
  }}
  .ri-card {{
    position: absolute; width: 92px; height: 116px; border-radius: 16px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
    background: rgba(255,255,255,.10);
    border: 1px solid rgba(255,255,255,.22);
    box-shadow: 0 20px 40px -18px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,255,255,.25);
    backdrop-filter: blur(6px);
    transform-style: preserve-3d;
  }}
  .ri-card .ico {{ font-size: 40px; filter: drop-shadow(0 6px 10px rgba(0,0,0,.4)); }}
  .ri-card .tag {{
    font-size: 13px; font-weight: 700; color: #fff; letter-spacing: .3px;
    padding: 3px 9px; border-radius: 999px;
    background: linear-gradient(110deg, {_ACCENT}, {_ACCENT_2});
    box-shadow: 0 6px 14px -6px rgba(34,211,238,.8);
  }}
  .c1 {{ left: 8%;  top: 26%; animation: ri-float1 6s ease-in-out infinite; }}
  .c2 {{ left: 34%; top: 12%; animation: ri-float2 7s ease-in-out infinite; }}
  .c3 {{ left: 60%; top: 30%; animation: ri-float3 6.5s ease-in-out infinite; }}
  .c4 {{ left: 30%; top: 50%; animation: ri-float2 8s ease-in-out infinite; opacity: .85; }}
  @keyframes ri-float1 {{ 0%,100% {{ transform: translateZ(40px) rotateY(-18deg) translateY(0); }} 50% {{ transform: translateZ(40px) rotateY(-18deg) translateY(-16px); }} }}
  @keyframes ri-float2 {{ 0%,100% {{ transform: translateZ(10px) rotateY(12deg) translateY(0); }} 50% {{ transform: translateZ(10px) rotateY(12deg) translateY(-22px); }} }}
  @keyframes ri-float3 {{ 0%,100% {{ transform: translateZ(70px) rotateY(-8deg) translateY(0); }} 50% {{ transform: translateZ(70px) rotateY(-8deg) translateY(-12px); }} }}

  .ri-copy {{ position: absolute; left: 7%; top: 50%; transform: translateY(-50%); z-index: 2; }}
  .ri-copy h1 {{
    margin: 0; font-size: 44px; font-weight: 800; line-height: 1;
    background: linear-gradient(100deg, #ffffff, {_ACCENT_2}, {_ACCENT}, #ffffff);
    background-size: 200% auto; -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent; animation: ri-sheen 5s linear infinite;
    opacity: 0; transform: translateY(14px); animation: ri-sheen 5s linear infinite, ri-in .8s .1s forwards;
  }}
  .ri-copy p {{
    margin: 10px 0 0; font-size: 16px; color: #c9d2ff; font-weight: 500;
    opacity: 0; transform: translateY(14px); animation: ri-in .8s .35s forwards;
  }}
  @keyframes ri-sheen {{ to {{ background-position: 200% center; }} }}
  @keyframes ri-in {{ to {{ opacity: 1; transform: translateY(0); }} }}

  @media (prefers-reduced-motion: reduce) {{
    .ri-bg, .ri-bg::after, .ri-card, .ri-copy h1, .ri-copy p {{ animation: none !important; }}
    .ri-copy h1, .ri-copy p {{ opacity: 1; transform: none; }}
  }}
</style>
<script>
  // Subtle mouse parallax — tilt the whole card stage toward the cursor.
  const hero = document.getElementById('ri-hero');
  const stage = hero.querySelector('.ri-stage');
  hero.addEventListener('mousemove', (e) => {{
    const r = hero.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5;
    const y = (e.clientY - r.top) / r.height - 0.5;
    stage.style.transform = `translateY(-50%) rotateY(${{x * 16}}deg) rotateX(${{-y * 12}}deg)`;
  }});
  hero.addEventListener('mouseleave', () => {{ stage.style.transform = 'translateY(-50%)'; }});
</script>
"""


def render_hero() -> None:
    """Render the 3D animated welcome hero at the top of the page."""
    components.html(_HERO_HTML, height=252)
