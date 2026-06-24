# watchlist.py ── StockLens Pro · Watchlist backed by Cloud Firestore

import streamlit as st
import yfinance as yf

from firebase_service import get_db
from user_service import update_watchlist_count

try:
    from firebase_admin import firestore as fb_firestore
    _FS_AVAILABLE = True
except ImportError:
    _FS_AVAILABLE = False

# In-memory fallback when Firestore unavailable
_local_watchlists: dict = {}


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_watchlist(uid: str) -> list:
    db = get_db()
    if db is None:
        return list(_local_watchlists.get(uid, []))
    try:
        doc = db.collection("watchlists").document(uid).get()
        if doc.exists:
            return doc.to_dict().get("stocks", [])
        return []
    except Exception:
        return list(_local_watchlists.get(uid, []))


def save_watchlist(uid: str, tickers: list):
    deduped = list(dict.fromkeys(t.upper().strip() for t in tickers if t.strip()))
    db = get_db()
    if db is None:
        _local_watchlists[uid] = deduped
        return
    try:
        server_ts = fb_firestore.SERVER_TIMESTAMP if _FS_AVAILABLE else None
        doc_ref   = db.collection("watchlists").document(uid)
        existing  = doc_ref.get()
        payload   = {"stocks": deduped, "updated_at": server_ts}
        if not existing.exists:
            payload["created_at"] = server_ts
        doc_ref.set(payload, merge=True)
        update_watchlist_count(uid, len(deduped))
    except Exception:
        _local_watchlists[uid] = deduped


def add_to_watchlist(uid: str, ticker: str):
    wl     = get_watchlist(uid)
    ticker = ticker.upper().strip()
    if ticker and ticker not in wl:
        wl.append(ticker)
        save_watchlist(uid, wl)


def remove_from_watchlist(uid: str, ticker: str):
    wl = [t for t in get_watchlist(uid) if t != ticker.upper().strip()]
    save_watchlist(uid, wl)


def is_in_watchlist(uid: str, ticker: str) -> bool:
    return ticker.upper().strip() in get_watchlist(uid)


# ── Quick direction prediction ────────────────────────────────────────────────

def _quick_direction(ticker: str):
    """5-day EMA + RSI momentum signal. Returns (direction, curr, pred, sym)."""
    try:
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty or len(hist) < 20:
            return "—", 0.0, 0.0, ""
        close = hist["Close"]
        curr  = float(close.iloc[-1])
        ema5  = close.ewm(span=5).mean().iloc[-1]
        ema20 = close.ewm(span=20).mean().iloc[-1]
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean().iloc[-1]
        loss  = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
        rsi   = 100 - (100 / (1 + gain / max(loss, 1e-9)))
        score = (1 if ema5 > ema20 else -1) + (1 if rsi < 60 else -1 if rsi > 70 else 0)
        direction = "UP" if score >= 0 else "DOWN"
        vol       = close.pct_change().std() * 100
        delta_pct = abs(vol) * (1 if direction == "UP" else -1)
        predicted = curr * (1 + delta_pct / 100)
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


# ── Sidebar render ────────────────────────────────────────────────────────────

def render_watchlist_panel(user: dict, C: dict):
    """
    Renders the full watchlist panel in the sidebar.
    user dict must have 'uid' key (or legacy 'email' for compat).
    Returns card_data list for alert sending.
    """
    uid = user.get("uid") or user.get("email", "")
    wl  = get_watchlist(uid)

    st.sidebar.markdown(
        '<div style="font-family:\'Syne\',sans-serif;font-size:0.85rem;'
        'font-weight:700;color:var(--teal);margin:4px 0 10px 0;'
        'letter-spacing:0.5px;">❤️ MY WATCHLIST</div>',
        unsafe_allow_html=True,
    )

    cols     = st.sidebar.columns([3, 1])
    new_tick = cols[0].text_input(
        "Add ticker", placeholder="e.g. TCS.NS",
        label_visibility="collapsed", key="wl_add_input",
    )
    if cols[1].button("➕", key="wl_add_btn", help="Add to watchlist"):
        if new_tick.strip():
            add_to_watchlist(uid, new_tick.strip())
            st.rerun()

    if not wl:
        st.sidebar.markdown(
            '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.72rem;'
            'color:var(--dim);text-align:center;padding:16px 0;">'
            'No stocks yet.<br>Search a ticker above and click ❤️</div>',
            unsafe_allow_html=True,
        )
        return []

    cards_html = '<div class="wl-grid">'
    card_data  = []

    for t in wl:
        direction, curr_p, pred_p, sym = _quick_direction(t)
        pct       = ((pred_p - curr_p) / curr_p * 100) if curr_p else 0
        up        = direction == "UP"
        clr       = C["green"] if up else C["red"]
        dir_class = "wl-card-up" if up else "wl-card-down"
        arrow     = "↑" if up else "↓"
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
            "curr": curr_p, "pred": pred_p, "pct": pct, "sym": sym,
        })

    cards_html += "</div>"
    st.sidebar.markdown(cards_html, unsafe_allow_html=True)

    with st.sidebar.expander("🗑️ Remove from Watchlist"):
        for t in wl:
            if st.button(f"✕  {t}", key=f"wl_rm_{t}", use_container_width=True):
                remove_from_watchlist(uid, t)
                st.rerun()

    return card_data
