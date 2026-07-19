import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from theme import get_theme

st.set_page_config(page_title="About · StockLens Pro", layout="wide", initial_sidebar_state="collapsed")

mode = st.session_state.get("theme_mode", "dark")
C, _, CSS = get_theme(mode)

st.html(CSS)

st.html(f"""
<style>
  .about-wrap {{
    max-width: 720px;
    margin: 4rem auto;
    padding: 0 1.5rem;
  }}
  .about-back {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.72rem;
    color: var(--dim);
    text-decoration: none;
    border: 1px solid var(--border);
    padding: 4px 14px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.08em;
    transition: all 0.2s;
    margin-bottom: 2.5rem;
    cursor: pointer;
  }}
  .about-back:hover {{ border-color: var(--teal); color: var(--teal); }}
  .about-hero-logo {{
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    color: var(--teal);
    letter-spacing: -2px;
    line-height: 1;
    margin-bottom: 0.4rem;
  }}
  .about-hero-logo em {{ color: var(--purple); font-style: normal; }}
  .about-hero-logo span {{
    font-size: 0.6rem;
    color: var(--dim);
    font-family: 'IBM Plex Mono', monospace;
    vertical-align: middle;
    margin-left: 6px;
    letter-spacing: 0.1em;
  }}
  .about-tagline {{
    font-size: 1rem;
    color: var(--dim);
    margin-bottom: 3rem;
    line-height: 1.5;
  }}
  .about-divider {{
    height: 1px;
    background: linear-gradient(to right, {C['teal_dim']}, transparent);
    margin: 2.5rem 0;
  }}
  .about-section-label {{
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--teal);
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 1rem;
    font-family: 'IBM Plex Mono', monospace;
  }}
  .about-section-body {{
    font-size: 0.92rem;
    color: {C['text_mid']};
    line-height: 1.8;
  }}
  .about-features {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 1.5rem;
  }}
  .about-feature-pill {{
    background: {C['teal_dim']};
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    font-size: 0.75rem;
    color: var(--teal);
    font-family: 'IBM Plex Mono', monospace;
  }}
  .about-footer {{
    margin-top: 3rem;
    font-size: 0.68rem;
    color: var(--dim);
    text-align: center;
    padding-top: 1.5rem;
    border-top: 1px solid var(--grid);
  }}
  @media (max-width: 640px) {{
    .about-wrap {{ margin: 2rem auto; padding: 0 0.25rem; }}
    .about-back {{ margin-bottom: 1.75rem; }}
    .about-hero-logo {{ font-size: 2.2rem; }}
    .about-tagline {{ font-size: 0.9rem; margin-bottom: 2rem; }}
    .about-features {{ grid-template-columns: 1fr; gap: 0.65rem; }}
    .about-section-body {{ font-size: 0.86rem; line-height: 1.7; }}
  }}
</style>

<div class="about-wrap">
  <a class="about-back" href="/" target="_top">&#8592; Back to App</a>

  <div class="about-hero-logo">stock<em>lens</em><span>PRO</span></div>
  <div class="about-tagline">Institutional-grade stock research. Built for everyone.</div>

  <div class="about-divider"></div>

  <div class="about-section-label">About the Project</div>
  <div class="about-section-body">
    StockLens Pro is an AI-powered stock research platform built for retail investors in India and globally.
    It combines real-time market data, technical analysis, machine learning forecasts, risk scoring, and
    fundamental screening into a single unified interface — so you can make informed decisions without
    juggling multiple tools or data sources.
    <br><br>
    From candlestick charts with moving averages to ML-based price forecasts, sentiment analysis, backtesting,
    and comparison tools — everything you need is in one place, free of charge.
  </div>

  <div class="about-features">
    <div class="about-feature-pill">&#128200; Real-time Price &amp; Volume</div>
    <div class="about-feature-pill">&#129302; ML Price Forecast</div>
    <div class="about-feature-pill">&#128269; Technical Analysis</div>
    <div class="about-feature-pill">&#9888; Risk &amp; Volatility Scoring</div>
    <div class="about-feature-pill">&#128240; News &amp; Sentiment</div>
    <div class="about-feature-pill">&#128202; Fundamental Screening</div>
  </div>

  <div class="about-divider"></div>

  <div class="about-section-label">Our Vision</div>
  <div class="about-section-body">
    We believe institutional-grade market intelligence should be accessible to everyone — not just
    professionals with Bloomberg terminals. StockLens Pro aims to democratise stock research,
    giving every investor the data, signals, and clarity they need to invest with confidence.
    <br><br>
    Our goal is to become the go-to research companion for the next generation of self-directed investors,
    levelling the playing field between retail and institutional participants — one chart at a time.
  </div>

</div>
""")
