# watchlist.py  ── StockLens Pro · Personal Watchlist (JSON-based)

import os
import json
import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd

WATCHLIST_DIR = os.path.join(os.path.dirname(__file__), "watchlists")


def _user_file(email: str) -> str:
    safe = email.replace("@", "_at_").replace(".", "_")
    os.makedirs(WATCHLIST_DIR, exist_ok=True)
    return os.path.join(WATCHLIST_DIR, f"{safe}.json")


def get_watchlist(email: str) -> list[str]:
    """Return list of ticker strings for this user."""
    path = _user_file(email)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []


def save_watchlist(email: str, tickers: list[str]):
    with open(_user_file(email), "w") as f:
        json.dump(list(dict.fromkeys(tickers)), f)   # de-dup, preserve order


def add_to_watchlist(email: str, ticker: str):
    wl = get_watchlist(email)
    ticker = ticker.upper().strip()
    if ticker and ticker not in wl:
        wl.append(ticker)
        save_watchlist(email, wl)


def remove_from_watchlist(email: str, ticker: str):
    wl = get_watchlist(email)
    wl = [t for t in wl if t != ticker.upper()]
    save_watchlist(email, wl)


def is_in_watchlist(email: str, ticker: str) -> bool:
    return ticker.upper() in get_watchlist(email)


# ── Quick 1-day prediction: +ret or -ret ─────────────────────────────────────
def _quick_direction(ticker: str) -> tuple[str, float, float, str]:
    """
    Returns (direction, current_price, predicted_price, currency_symbol).
    direction is 'UP' or 'DOWN'.
    Uses a simple 5-day momentum signal — fast, no full ML needed.
    """
    try:
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty or len(hist) < 20:
            return "—", 0.0, 0.0, ""
        close = hist["Close"]
        curr  = float(close.iloc[-1])
        # Momentum: 5-day EMA > 20-day EMA → UP
        ema5  = close.ewm(span=5).mean().iloc[-1]
        ema20 = close.ewm(span=20).mean().iloc[-1]
        # RSI signal
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean().iloc[-1]
        loss  = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rsi   = 100 - (100 / (1 + gain / max(loss, 1e-9)))
        # Combine signals
        score = (1 if ema5 > ema20 else -1) + (1 if rsi < 60 else -1 if rsi > 70 else 0)
        direction = "UP" if score >= 0 else "DOWN"
        # Estimate next-day price (small ±0.5–1.5% move)
        vol   = close.pct_change().std() * 100
        delta_pct = abs(vol) * (1 if direction == "UP" else -1)
        predicted = curr * (1 + delta_pct / 100)
        # Currency symbol
        info = {}
        try:
            info = yf.Ticker(ticker).info
        except Exception:
            pass
        currency = info.get("currency", "USD")
        sym = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
        return direction, curr, predicted, sym
    except Exception:
        return "—", 0.0, 0.0, ""


# ── 3D Premium Watchlist Panel ────────────────────────────────────────────────
def render_watchlist_panel(user: dict, C: dict):
    """
    Renders the full watchlist panel in the sidebar.
    Shows 3D glowing cards for each ticker.
    """
    email = user["email"]
    wl    = get_watchlist(email)

    st.sidebar.markdown(
        '<div style="font-family:\'Syne\',sans-serif;font-size:0.85rem;'
        'font-weight:700;color:var(--teal);margin:4px 0 10px 0;'
        'letter-spacing:0.5px;">❤️ MY WATCHLIST</div>',
        unsafe_allow_html=True,
    )

    # ── Add new ticker ────────────────────────────────────────────────────────
    cols = st.sidebar.columns([3, 1])
    new_tick = cols[0].text_input(
        "Add ticker", placeholder="e.g. TCS.NS", label_visibility="collapsed",
        key="wl_add_input"
    )
    if cols[1].button("➕", key="wl_add_btn", help="Add to watchlist"):
        if new_tick.strip():
            add_to_watchlist(email, new_tick.strip().upper())
            st.rerun()

    if not wl:
        st.sidebar.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;'
            'color:var(--dim);text-align:center;padding:16px 0;">'
            'No stocks yet.<br>Search a ticker above and click ❤️</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Render 3D cards (2-column grid) ──────────────────────────────────────
    cards_html = '<div class="wl-grid">'
    card_data  = []   # collect for alert use

    for t in wl:
        direction, curr_p, pred_p, sym = _quick_direction(t)
        pct = ((pred_p - curr_p) / curr_p * 100) if curr_p else 0
        up  = direction == "UP"
        clr = C["green"] if up else C["red"]
        dir_class = "wl-card-up" if up else "wl-card-down"
        arrow = "↑" if up else "↓"
        price_str = f"{sym}{curr_p:,.2f}" if curr_p else "—"
        pct_str   = f"{arrow} {abs(pct):.2f}%"

        cards_html += f"""
        <div class="wl-card {dir_class}">
          <div class="wl-ticker">{t}</div>
          <div class="wl-price">{price_str}</div>
          <div class="wl-chg" style="color:{clr}">{pct_str}</div>
          <div class="wl-dir">{arrow}</div>
        </div>"""

        card_data.append({
            "ticker": t, "direction": direction,
            "curr": curr_p, "pred": pred_p,
            "pct": pct, "sym": sym,
        })

    cards_html += "</div>"
    st.sidebar.markdown(cards_html, unsafe_allow_html=True)

    # ── Remove buttons ────────────────────────────────────────────────────────
    with st.sidebar.expander("🗑️ Remove from Watchlist"):
        for t in wl:
            if st.button(f"✕  {t}", key=f"wl_rm_{t}", use_container_width=True):
                remove_from_watchlist(email, t)
                st.rerun()

    return card_data
