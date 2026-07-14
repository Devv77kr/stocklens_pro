# app.py  ── StockLens Pro · Complete Market Intel

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

import indicators as ind
import models as mdl
import auth as sl_auth
import watchlist as sl_wl
import alerts as sl_alerts
import wishlist as sl_wish
import watchlist_service as wl_svc
from utils.cookies import get_cookie_manager

# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS & GMAIL ALERT
# ══════════════════════════════════════════════════════════════════════════════
def send_gmail_alert(sender_email, app_password, receiver_email, ticker, price, action, c_sym):
    subject = f"🚀 StockLens Pro Alert: {ticker} {action}"
    body = (f"StockLens Pro has detected a major signal!\n\n"
            f"Ticker: {ticker}\n"
            f"Action: {action}\n"
            f"Current Price: {c_sym}{price:.2f}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        return True
    except:
        return False

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & THEME SETUP
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="StockLens Pro",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

from theme import get_theme
C, PLOTLY_BASE, CSS = get_theme(st.session_state.theme_mode)

st.html(CSS)

def pb(name, **kw):
    layout = {**PLOTLY_BASE, **kw}
    return go.Figure(layout=layout)

def fmt_large(n):
    if n is None: return "N/A"
    try:   n = float(n)
    except: return "N/A"
    if abs(n) >= 1e12: return f"{n/1e12:.2f}T"
    if abs(n) >= 1e9:  return f"{n/1e9:.2f}B"
    if abs(n) >= 1e6:  return f"{n/1e6:.2f}M"
    return f"{n:,.0f}"

def card(label, value, sub="", val_color=None):
    vc = val_color or C["text"]
    return f"""
    <div class="metric-card">
      <div class="m-label">{label}</div>
      <div class="m-value" style="color:{vc}">{value}</div>
      {"<div class='m-sub'>"+sub+"</div>" if sub else ""}
    </div>"""

def sec(title, icon=""):
    st.html(f'<div class="sec-title">{icon} {title}</div>')

@st.cache_data(ttl=300, show_spinner=False)
def load_stock(ticker, period="2y"):
    tk   = yf.Ticker(ticker)
    hist = tk.history(period=period)
    info = tk.info
    return hist, info

@st.cache_data(ttl=300, show_spinner=False)
def load_multi(tickers, period="1y"):
    out = {}
    for t in tickers:
        try:
            h = yf.Ticker(t).history(period=period)
            if not h.empty: out[t] = h["Close"]
        except: pass
    return pd.DataFrame(out)

def pct_color(v):
    return C["teal"] if v >= 0 else C["red"]

# ══════════════════════════════════════════════════════════════════════════════
# FIREBASE + SESSION RESTORE + OAUTH CALLBACK
# ══════════════════════════════════════════════════════════════════════════════
sl_auth.initialize_firebase_auth()
# 0. Handle topbar dropdown logout (?action=logout link).
if st.query_params.get("action") == "logout":
    st.query_params.clear()
    sl_auth.logout(None)   # clears session + reruns; cookie cleared on next cookie_manager init
# 1. Process OAuth ?code= BEFORE CookieManager init (cookie_manager=None is safe).
#    CookieManager.init causes a page reload (new WebSocket = new session_state).
#    If code exchange runs after that reload, the code gets retried → invalid_grant
#    (error disappears instantly because st.query_params.clear() triggers another
#    rerun, so user sees "not logged in, no errors").
sl_auth.handle_oauth_callback(None)
# 2. Init CookieManager AFTER code exchange (may trigger its own internal rerun).
_cookie_manager = get_cookie_manager()
# 3. Restore returning-user session from cookie.
sl_auth.restore_session_from_cookie(_cookie_manager)
# 4. Write cookie now that manager is ready (skipped if already saved this session).
sl_auth.maybe_save_cookie(_cookie_manager)

# ══════════════════════════════════════════════════════════════════════════════
# TOPBAR
# ══════════════════════════════════════════════════════════════════════════════
now           = datetime.now().strftime("%H:%M:%S  %d %b %Y")
_auth_badge   = sl_auth.render_auth_button(C)
_sep          = f'<span style="color:{C["border"]}">|</span>'
_topbar_html  = f"""
<div class="topbar">
  <div class="logo">stock<em>lens</em> <span style="font-size:0.55rem;color:{C['text_dim']};font-family:'IBM Plex Mono'">PRO</span></div>
  <nav class="topbar-nav">
    <a href="/about" target="_top" class="topbar-nav-btn" style="text-decoration:none;">About</a>
  </nav>
  <div class="topbar-right">
    {_auth_badge}
    {_sep}
    <div class="live-dot"></div>
    <span>LIVE DATA</span>
    <span style="color:{C['border']}">|</span>
    <span>{now}</span>
  </div>
</div>
"""
st.html(_topbar_html)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL SEARCH BAR (MAIN SCREEN)
# ══════════════════════════════════════════════════════════════════════════════
st.html("<br>")
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    ticker = st.text_input("🔍 Search any Stock Ticker", "RELIANCE.NS", 
                           help="US: AAPL, TSLA | India: RELIANCE.NS, TCS.NS").upper().strip()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── 1. GOOGLE SIGN IN ─────────────────────────────────────────────────────────
    sl_current_user = sl_auth.render_auth_panel(C, _cookie_manager)
    st.sidebar.markdown("---")

    # ── 2. WATCHLIST PANEL (only when signed in) ───────────────────────────
    _wl_card_data = None
    if sl_current_user:
        _wl_card_data = sl_wl.render_watchlist_panel(sl_current_user, C)
        st.sidebar.markdown("---")

    # ── 3. DASHBOARD CONTROLS ────────────────────────────────────────────────────
    st.sidebar.markdown("### ⚙️ Dashboard Controls")
    theme_choice = st.sidebar.radio("🌓 Theme Mode", ["Dark", "Light"],
                             index=0 if st.session_state.theme_mode == "dark" else 1,
                             horizontal=True)
    if theme_choice.lower() != st.session_state.theme_mode:
        st.session_state.theme_mode = theme_choice.lower()
        st.rerun()
    st.sidebar.markdown("---")

    period_opts = {"1 Month":"1mo","3 Months":"3mo","6 Months":"6mo",
                   "1 Year":"1y","2 Years":"2y","5 Years":"5y","Max":"max"}
    period_lbl  = st.sidebar.selectbox("📅 Period", list(period_opts.keys()), index=4)
    period      = period_opts[period_lbl]
    chart_type  = st.sidebar.radio("📊 Chart", ["Candlestick","Line"], horizontal=True)
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🤖 ML Settings")
    horizon  = st.sidebar.slider("Forecast Days", 7, 90, 30)
    use_lstm = st.sidebar.toggle("Enable LSTM (slower)", value=False)
    mc_sims  = st.sidebar.slider("Monte Carlo Paths", 100, 2000, 500, step=100)
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🔀 Comparison")
    compare_raw     = st.sidebar.text_input("Compare Tickers", "MSFT, GOOGL, TCS.NS, INFY.NS")
    compare_tickers = [t.strip().upper() for t in compare_raw.split(",") if t.strip()]
    st.sidebar.markdown("---")

    # ── 4. SMART GMAIL ALERTS ────────────────────────────────────────────────────
    st.sidebar.markdown("#### 📧 Gmail Alerts")
    enable_gmail = st.sidebar.toggle("Enable Gmail Alerts", value=False)
    sender  = st.sidebar.text_input("Your Gmail", placeholder="example@gmail.com")
    app_pwd = st.sidebar.text_input("Gmail App Password", type="password",
                                    help="Google Account ➔ Security ➔ App Passwords")
    receiver = st.sidebar.text_input("Receiver Email", placeholder="notify-me@gmail.com")

    # Smart watchlist alert button
    if sl_current_user and _wl_card_data and enable_gmail:
        if st.sidebar.button("🔔 Alert My Watchlist Now",
                             use_container_width=True, key="wl_alert_btn"):
            _uname = sl_current_user.get("display_name",
                        sl_current_user.get("name", "Investor"))
            _uid   = st.session_state.get("uid", "")
            _ok, _msg = sl_alerts.send_watchlist_alert(
                sender, app_pwd, receiver, _uname, _wl_card_data, uid=_uid)
            if _ok:
                st.sidebar.markdown(
                    f'<div class="alert-sent">✅ {_msg}</div>',
                    unsafe_allow_html=True)
            else:
                st.sidebar.error(_msg)
    elif sl_current_user and not _wl_card_data:
        st.sidebar.caption("❤️ Add stocks to your watchlist to enable alerts.")
    elif not sl_current_user:
        st.sidebar.caption("🔐 Sign in to send watchlist alerts.")

    st.sidebar.markdown("---")
    rf_rate = st.sidebar.number_input("Risk-Free Rate (%)", 0.0, 15.0, 5.0, 0.25) / 100

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOAD & DYNAMIC CURRENCY
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner(f"⚡🔍︎ Loading {ticker}…"):
    try:
        hist, info = load_stock(ticker, period)
    except Exception as e:
        st.error(f"Failed to load **{ticker}**: {e}")
        st.stop()

if hist.empty:
    st.error(f"No data for **{ticker}**.")
    st.stop()

hist = hist.ffill().dropna()

if len(hist) < 2:
    st.error(f"Not enough clean data for **{ticker}**.")
    st.stop()

close  = hist["Close"]
high   = hist["High"]
low    = hist["Low"]
volume = hist["Volume"]
open_  = hist["Open"]

company = info.get("longName", ticker)
sector  = info.get("sector", "—")

# --- DYNAMIC CURRENCY LOGIC ---
curr_code = info.get("currency", "USD")
if curr_code == "INR": c_sym = "₹"
elif curr_code == "USD": c_sym = "$"
elif curr_code == "EUR": c_sym = "€"
elif curr_code == "GBP": c_sym = "£"
else: c_sym = curr_code + " "

curr    = close.iloc[-1]
prev    = close.iloc[-2]
chg     = curr - prev
chg_pct = chg / prev * 100

# ══════════════════════════════════════════════════════════════════════════════
# COMPANY HEADER & HEALTH SCORE
# ══════════════════════════════════════════════════════════════════════════════
_roe = info.get("returnOnEquity")
_roe = float(_roe) if _roe is not None else 0
if _roe > 0.15: q_sc, q_lbl, q_col = 85, "High", C["green"]
elif _roe > 0.05: q_sc, q_lbl, q_col = 50, "Average", C["yellow"]
else: q_sc, q_lbl, q_col = 20, "Low", C["red"]

_pe = info.get("trailingPE")
_pe = float(_pe) if _pe is not None else 25
if _pe < 20: v_sc, v_lbl, v_col = 90, "Attractive", C["green"]
elif _pe < 40: v_sc, v_lbl, v_col = 50, "Fair", C["yellow"]
else: v_sc, v_lbl, v_col = 15, "Expensive", C["red"]

_rev = info.get("revenueGrowth")
_rev = float(_rev) if _rev is not None else 0
if _rev > 0.10: t_sc, t_lbl, t_col = 80, "Positive", C["green"]
elif _rev > 0: t_sc, t_lbl, t_col = 50, "Flat", C["yellow"]
else: t_sc, t_lbl, t_col = 20, "Negative", C["red"]

tot_score = int((q_sc + v_sc + t_sc) / 3)
if tot_score >= 70: ovr_lbl, ovr_col = "STRONG", C["green"]
elif tot_score >= 40: ovr_lbl, ovr_col = "AVERAGE", C["yellow"]
else: ovr_lbl, ovr_col = "WEAK", C["red"]

head_col1, head_col2 = st.columns([2.5, 1.5])

with head_col1:
    arrow = "▲" if chg >= 0 else "▼"
    clr   = C["teal"] if chg >= 0 else C["red"]

    # ── Heart / Watchlist button ───────────────────────────────────────────
    _wl_uid  = st.session_state.get("uid", "")
    _in_wl   = bool(_wl_uid) and sl_wl.is_in_watchlist(_wl_uid, ticker)
    _heart   = "❤️" if _in_wl else "🤍"
    _heart_tip = "Remove from Watchlist" if _in_wl else "Add to Watchlist"

    _hcol1, _hcol2 = st.columns([10, 1])
    with _hcol1:
        st.html(f"""
        <div style="display:flex;align-items:baseline;gap:1.2rem;flex-wrap:wrap;margin-bottom:0.3rem;">
          <span style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;color:{C['text']};">{company}</span>
          <span style="color:{C['text_dim']};font-size:0.8rem;">{ticker} · {info.get('exchange','—')} · {sector}</span>
        </div>
        <div style="display:flex;align-items:baseline;gap:1rem;margin-bottom:1rem;">
          <span style="font-size:2.4rem;font-weight:600;color:{C['text']};">{c_sym}{curr:.2f}</span>
          <span style="color:{clr};font-size:1rem;font-weight:500;">{arrow} {c_sym}{chg:+.2f} ({chg_pct:+.2f}%)</span>
          <span style="color:{C['text_dim']};font-size:0.72rem;">as of {hist.index[-1].strftime('%d %b %Y')}</span>
        </div>""")
    with _hcol2:
        if _wl_uid:
            if st.button(_heart, key="wl_heart_btn", help=_heart_tip):
                if _in_wl:
                    sl_wl.remove_from_watchlist(_wl_uid, ticker)
                else:
                    sl_wl.add_to_watchlist(_wl_uid, ticker)
                st.rerun()

            # ── Wishlist / Price Alert button ──────────────────────────────
            _in_wish   = wl_svc.is_in_wishlist(_wl_uid, ticker)
            _wish_lbl  = "⭐" if _in_wish else "☆"
            _wish_tip  = "Manage Price Alert" if _in_wish else "Add to Wishlist (Price Alert)"
            if st.button(_wish_lbl, key="wish_star_btn", help=_wish_tip):
                st.session_state["open_wish_modal"] = ticker
        else:
            st.html(
                f'<span title="Sign in to add to watchlist" '
                f'style="font-size:1.4rem;opacity:0.3;cursor:not-allowed;">🤍</span>')

    # ── Wishlist modal (renders as dialog overlay) ─────────────────────────
    if st.session_state.get("open_wish_modal") == ticker and _wl_uid:
        sl_wish.render_add_to_wishlist_modal(_wl_uid, ticker, company, curr, c_sym, C)
        st.session_state.pop("open_wish_modal", None)

with head_col2:
    st.html(f"""
    <div style="background:var(--card); border:1px solid var(--border); border-radius:12px; padding:12px 18px; display:flex; gap:18px; align-items:center; float:right; width:100%; max-width:320px; box-shadow:0 4px 15px rgba(0,0,0,0.1);">
        <div style="text-align:center; min-width:60px;">
            <div style="width:55px; height:55px; border-radius:50%; border:4px solid {ovr_col}; display:flex; align-items:center; justify-content:center; font-size:1.4rem; font-weight:800; color:{C['text']}; margin:0 auto; font-family:'IBM Plex Mono', monospace;">
                {tot_score}
            </div>
            <div style="font-size:0.6rem; color:{ovr_col}; font-weight:700; margin-top:6px; letter-spacing:1px; font-family:'Syne',sans-serif;">{ovr_lbl}</div>
        </div>
        <div style="flex:1; display:flex; flex-direction:column; gap:6px; border-left:1px solid var(--grid); padding-left:15px; font-family:'IBM Plex Mono', monospace;">
            <div style="font-size:0.75rem; display:flex; justify-content:space-between; align-items:center;">
               <span style="color:var(--dim)">Quality</span> 
               <span style="background:{q_col}22; color:{q_col}; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.65rem;">{q_lbl}</span>
            </div>
            <div style="font-size:0.75rem; display:flex; justify-content:space-between; align-items:center;">
               <span style="color:var(--dim)">Valuation</span> 
               <span style="background:{v_col}22; color:{v_col}; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.65rem;">{v_lbl}</span>
            </div>
            <div style="font-size:0.75rem; display:flex; justify-content:space-between; align-items:center;">
               <span style="color:var(--dim)">Fin Trend</span> 
               <span style="background:{t_col}22; color:{t_col}; padding:2px 8px; border-radius:4px; font-weight:600; font-size:0.65rem;">{t_lbl}</span>
            </div>
        </div>
    </div>
    """)

# ── Metric row ────────────────────────────────────────────────────────────────
mkt_cap  = fmt_large(info.get("marketCap"))
pe       = f"{info.get('trailingPE',0):.1f}x" if info.get("trailingPE") else "N/A"
eps      = f"{c_sym}{info.get('trailingEps',0):.2f}" if info.get("trailingEps") else "N/A"
wk52hi   = info.get("fiftyTwoWeekHigh",0)
wk52lo   = info.get("fiftyTwoWeekLow",0)
beta     = f"{info.get('beta',0):.2f}" if info.get("beta") else "N/A"
div_y    = f"{info.get('dividendYield',0)*100:.2f}%" if info.get("dividendYield") else "N/A"
avg_vol  = fmt_large(info.get("averageVolume"))
fwd_pe   = f"{info.get('forwardPE',0):.1f}x" if info.get("forwardPE") else "N/A"
peg      = f"{info.get('pegRatio',0):.2f}" if info.get("pegRatio") else "N/A"
pb_ratio = f"{info.get('priceToBook',0):.2f}" if info.get("priceToBook") else "N/A"
ev_ebitda= f"{info.get('enterpriseToEbitda',0):.1f}x" if info.get("enterpriseToEbitda") else "N/A"

cards_data = [
    ("Market Cap",     mkt_cap,    f"P/E: {pe}  |  Fwd P/E: {fwd_pe}"),
    ("52W Range",      f"{c_sym}{wk52lo:.0f}–{c_sym}{wk52hi:.0f}", f"Beta: {beta}  |  PEG: {peg}"),
    ("EPS / P/B",      f"{eps}  /  {pb_ratio}", f"EV/EBITDA: {ev_ebitda}"),
    ("Avg Volume",     avg_vol,    f"Div Yield: {div_y}"),
]
cols = st.columns(4)
for col, (lbl, val, sub) in zip(cols, cards_data):
    with col:
        st.html(card(lbl, val, sub))

st.html("<div style='height:0.5rem'></div>")

# ── COMPANY SUMMARY ───────────────────────────────────────────────────────────
summary = info.get("longBusinessSummary", "Company summary not available.")
website = info.get("website", "#")
industry = info.get("industry", sector)
employees = info.get("fullTimeEmployees", "N/A")
if employees != "N/A":
    employees = f"{int(employees):,}"  # Formats number with commas (e.g., 100,000)
city = info.get("city", "")
country = info.get("country", "")
location = f"{city}, {country}".strip(", ")
if location == ",": location = "Global"

# HTML/CSS for a Premium Article-style layout
about_html = f"""
<div style="background:var(--card); border:1px solid var(--border); border-radius:12px; padding:1.8rem; margin-top:0.5rem; box-shadow:0 8px 24px rgba(0,0,0,0.15);">
    <div style="display:flex; justify-content:space-between; align-items:flex-end; border-bottom:1px solid var(--grid); padding-bottom:1.2rem; margin-bottom:1.5rem; flex-wrap:wrap; gap:1rem;">
        <div>
            <div style="font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:var(--text); margin-bottom:0.8rem; letter-spacing:-0.5px;">About {company}</div>
            <div style="display:flex; gap:8px; flex-wrap:wrap;">
                <span style="background:rgba(0,255,224,0.1); color:var(--teal); border:1px solid rgba(0,255,224,0.2); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:600; font-family:'IBM Plex Mono', monospace;">🏛️ {industry}</span>
                <span style="background:rgba(168,85,247,0.1); color:var(--purple); border:1px solid rgba(168,85,247,0.2); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:600; font-family:'IBM Plex Mono', monospace;">📍 {location or 'Global'}</span>
                <span style="background:rgba(249,115,22,0.1); color:var(--orange); border:1px solid rgba(249,115,22,0.2); padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:600; font-family:'IBM Plex Mono', monospace;">👥 {employees} Employees</span>
            </div>
        </div>
        <a href="{website}" target="_blank" style="text-decoration:none;">
            <div style="background:var(--bg2); border:1px solid var(--border); padding:8px 16px; border-radius:8px; color:var(--teal); font-size:0.8rem; font-weight:600; font-family:'IBM Plex Mono', monospace; transition:0.3s; box-shadow:0 2px 8px rgba(0,255,224,0.1);">
                🌐 Visit Website ↗
            </div>
        </a>
    </div>
    <div style="font-family:'IBM Plex Mono', monospace; font-size:0.85rem; line-height:1.8; color:var(--text); text-align:justify; opacity:0.9;">
        <span style="float:left; font-family:'Syne',sans-serif; font-size:3.5rem; line-height:0.8; padding-right:10px; padding-top:6px; color:var(--teal); font-weight:800; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">{summary[0] if summary else ''}</span>
        {summary[1:] if summary else ''}
    </div>
</div>
"""

with st.expander("📖 Read Professional Company Profile", expanded=False):
    st.html(about_html)

# ── Signal pills & Gmail Alerts ───────────────────────────────────────────────
signals = ind.generate_signals(hist)
pill_html = '<div class="signal-row">'
buy_c = sum(1 for v in signals.values() if v[0] == "BUY")
sell_c= sum(1 for v in signals.values() if v[0] == "SELL")
overall_cls = "sig-buy" if buy_c > sell_c else ("sig-sell" if sell_c > buy_c else "sig-hold")
overall_lbl = "OVERALL: BUY" if buy_c > sell_c else ("OVERALL: SELL" if sell_c > buy_c else "OVERALL: HOLD")
pill_html += f'<span class="signal {overall_cls}" style="font-size:0.78rem;padding:5px 18px;">{overall_lbl} ({buy_c}↑ / {sell_c}↓)</span>'
for name, (sig, cls, tip) in signals.items():
    pill_html += f'<span class="signal {cls}" title="{tip}">{name}: {sig}</span>'
pill_html += "</div>"
st.html(pill_html)

# ▼▼▼ GMAIL ALERT LOGIC ▼▼▼
if enable_gmail and overall_lbl == "OVERALL: BUY" and sender and app_pwd and receiver:
    alert_key = f"email_{ticker}_BUY"
    if st.session_state.get('last_email_alert') != alert_key:
        with st.spinner("📧 Sending Gmail Alert..."):
            success = send_gmail_alert(sender, app_pwd, receiver, ticker, curr, "BUY", c_sym)
            if success:
                st.toast(f"✅ Alert sent to {receiver}!", icon="📧")
                st.session_state['last_email_alert'] = alert_key
            else:
                st.error("Failed to send email. Check your App Password.") 

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tabs = st.tabs([
    "📈 Price & Volume",
    "📡 Technical Analysis",
    "🤖 ML Forecast",
    "⚠️ Risk Analysis",
    "🔀 Comparison",
    "📋 Fundamentals",
    "🎯 Backtesting",
    "📰 News & Sentiment",
    "⭐ Wishlist & Alerts",
])

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 1 · Price & Volume
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    sec("Price Chart", "📈")

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.60, 0.22, 0.18], vertical_spacing=0.02,
        subplot_titles=("", "Volume", "OBV"),
    )

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=hist.index, open=open_, high=high, low=low, close=close,
            increasing=dict(line=dict(color=C["teal"]), fillcolor=C["teal_dim"]),
            decreasing=dict(line=dict(color=C["red"]),  fillcolor=C["red_dim"]),
            name="OHLC",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=hist.index, y=close, name="Close",
            line=dict(color=C["teal"], width=1.8),
            fill="tozeroy", fillcolor="rgba(0,255,224,0.04)",
        ), row=1, col=1)

    for n, color, dash in [(20, C["orange"], "dot"), (50, C["purple"], "dash"), (200, C["blue"], "dashdot")]:
        ma = ind.sma(close, n)
        fig.add_trace(go.Scatter(x=hist.index, y=ma, name=f"MA{n}",
            line=dict(color=color, width=1.2, dash=dash), opacity=0.85), row=1, col=1)

    bb_lo, bb_mid, bb_hi = ind.bollinger_bands(close)
    fig.add_trace(go.Scatter(x=hist.index, y=bb_hi, name="BB Upper",
        line=dict(color="rgba(168,85,247,0.5)", width=1, dash="dot"), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=bb_lo, name="BB Lower",
        line=dict(color="rgba(168,85,247,0.5)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(168,85,247,0.04)", showlegend=False), row=1, col=1)

    vol_clr = [C["teal"] if c >= o else C["red"] for c, o in zip(close, open_)]
    fig.add_trace(go.Bar(x=hist.index, y=volume, name="Volume",
        marker_color=vol_clr, marker_opacity=0.7, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=hist.index, y=volume.rolling(20).mean(), name="Vol MA20",
        line=dict(color=C["orange"], width=1.2), showlegend=False), row=2, col=1)

    obv_vals = ind.obv(close, volume)
    fig.add_trace(go.Scatter(x=hist.index, y=obv_vals, name="OBV",
        line=dict(color=C["purple"], width=1.5), showlegend=False,
        fill="tozeroy", fillcolor="rgba(168,85,247,0.05)"), row=3, col=1)

    fig.update_layout(**PLOTLY_BASE, height=600,
                      xaxis_rangeslider_visible=False,
                      yaxis_title=f"Price ({curr_code})",
                      yaxis2_title="Volume",
                      yaxis3_title="OBV")
    fig.update_xaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    sec("Period Statistics", "📊")
    period_ret = (close.iloc[-1] / close.iloc[0] - 1) * 100
    ann_vol    = close.pct_change().std() * np.sqrt(252) * 100
    max_dd_val = ((close / close.cummax()) - 1).min() * 100
    avg_daily  = close.pct_change().mean() * 100

    stat_cols = st.columns(6)
    stat_data = [
        ("Period High",   f"{c_sym}{high.max():.2f}",         C["teal"]),
        ("Period Low",    f"{c_sym}{low.min():.2f}",           C["red"]),
        ("Period Return", f"{period_ret:+.1f}%",         pct_color(period_ret)),
        ("Ann. Volatility",f"{ann_vol:.1f}%",            C["orange"]),
        ("Max Drawdown",  f"{max_dd_val:.1f}%",          C["red"]),
        ("Avg Daily Ret", f"{avg_daily:+.3f}%",          pct_color(avg_daily)),
    ]
    for col, (lbl, val, clr) in zip(stat_cols, stat_data):
        with col:
            st.html(f"""<div class="metric-card" style="text-align:center">
              <div class="m-label">{lbl}</div>
              <div style="font-size:1.2rem;font-weight:600;color:{clr}">{val}</div>
            </div>""")

    st.html("<div style='height:0.5rem'></div>")
    d1, d2 = st.columns([1, 2])
    with d1:
        sec("Day Distribution", "🍩")
        daily_ret = close.pct_change().dropna()
        up   = int((daily_ret > 0).sum())
        dn   = int((daily_ret < 0).sum())
        flat = int((daily_ret == 0).sum())
        donut = go.Figure(go.Pie(
            labels=["Up Days","Down Days","Flat"],
            values=[up, dn, flat], hole=0.6,
            marker=dict(colors=[C["teal"], C["red"], C["yellow"]]),
            textinfo="percent+label", textfont=dict(size=10),
        ))
        donut.update_layout(**{k:v for k,v in PLOTLY_BASE.items() if k not in ("xaxis","yaxis","margin")},
            height=260, margin=dict(l=0,r=0,t=10,b=10),
            annotations=[dict(text=f"{up+dn+flat}<br>days",
                              x=0.5,y=0.5,showarrow=False,
                              font=dict(size=13,color=C["text_dim"]))])
        st.plotly_chart(donut, use_container_width=True)

    with d2:
        sec("Return Distribution", "📉")
        hist_fig = go.Figure()
        hist_fig.add_trace(go.Histogram(
            x=daily_ret * 100, nbinsx=70,
            marker_color=C["purple"], marker_opacity=0.75, name="Daily Return %",
        ))
        mean_val = daily_ret.mean() * 100
        hist_fig.add_trace(go.Scatter(
            x=[mean_val, mean_val], y=[0, 1],
            mode="lines", yaxis="y",
            line=dict(color=C["teal"], width=1.5, dash="dash"),
            name="Mean", showlegend=False,
        ))
        hist_fig.update_layout(**PLOTLY_BASE, height=260,
            xaxis_title="Daily Return (%)", yaxis_title="Count", bargap=0.04)
        st.plotly_chart(hist_fig, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 2 · Technical Analysis
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    sec("Technical Indicators Dashboard", "📡")

    rsi_vals   = ind.rsi(close)
    macd_l, macd_s, macd_h = ind.macd(close)
    stoch_k, stoch_d        = ind.stochastic(high, low, close)
    wr_vals    = ind.williams_r(high, low, close)
    cci_vals   = ind.cci(high, low, close)
    atr_vals   = ind.atr(high, low, close)
    mfi_vals   = ind.mfi(high, low, close, volume)

    fig2 = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.30, 0.25, 0.23, 0.22],
        subplot_titles=("RSI (14)", "MACD (12,26,9)", "Stochastic (14,3)", "Williams %R / CCI"),
    )

    fig2.add_trace(go.Scatter(x=hist.index, y=rsi_vals, name="RSI",
        line=dict(color=C["teal"], width=1.8)), row=1, col=1)
    fig2.add_hrect(y0=70, y1=100, fillcolor="rgba(255,77,109,0.08)", line_width=0, row=1, col=1)
    fig2.add_hrect(y0=0,  y1=30,  fillcolor="rgba(0,255,224,0.08)", line_width=0, row=1, col=1)
    fig2.add_hline(y=70, line_dash="dash", line_color=C["red"],  line_width=1, row=1, col=1)
    fig2.add_hline(y=30, line_dash="dash", line_color=C["teal"], line_width=1, row=1, col=1)
    fig2.add_hline(y=50, line_dash="dot",  line_color=C["text_dim"], line_width=0.8, row=1, col=1)

    macd_bar_clr = [C["teal"] if v >= 0 else C["red"] for v in macd_h]
    fig2.add_trace(go.Bar(x=hist.index, y=macd_h, name="Histogram",
        marker_color=macd_bar_clr, marker_opacity=0.7, showlegend=False), row=2, col=1)
    fig2.add_trace(go.Scatter(x=hist.index, y=macd_l, name="MACD",
        line=dict(color=C["blue"], width=1.5)), row=2, col=1)
    fig2.add_trace(go.Scatter(x=hist.index, y=macd_s, name="Signal",
        line=dict(color=C["orange"], width=1.5, dash="dash")), row=2, col=1)

    fig2.add_trace(go.Scatter(x=hist.index, y=stoch_k, name="%K",
        line=dict(color=C["purple"], width=1.5)), row=3, col=1)
    fig2.add_trace(go.Scatter(x=hist.index, y=stoch_d, name="%D",
        line=dict(color=C["orange"], width=1.2, dash="dash")), row=3, col=1)
    fig2.add_hline(y=80, line_dash="dash", line_color=C["red"],  line_width=1, row=3, col=1)
    fig2.add_hline(y=20, line_dash="dash", line_color=C["teal"], line_width=1, row=3, col=1)

    fig2.add_trace(go.Scatter(x=hist.index, y=wr_vals, name="W%R",
        line=dict(color=C["yellow"], width=1.3)), row=4, col=1)
    fig2.add_hline(y=-20, line_dash="dot", line_color=C["red"],  line_width=1, row=4, col=1)
    fig2.add_hline(y=-80, line_dash="dot", line_color=C["teal"], line_width=1, row=4, col=1)

    fig2.update_layout(**PLOTLY_BASE, height=750, showlegend=True)
    fig2.update_yaxes(range=[0, 100], row=1, col=1)
    fig2.update_yaxes(range=[-100, 0], row=4, col=1)
    st.plotly_chart(fig2, use_container_width=True)

    sec("Volatility & Money Flow", "💹")
    c1, c2 = st.columns(2)
    with c1:
        fig_atr = pb("ATR")
        fig_atr.add_trace(go.Scatter(x=hist.index, y=atr_vals, name="ATR (14)",
            line=dict(color=C["orange"], width=1.6),
            fill="tozeroy", fillcolor="rgba(249,115,22,0.07)"))
        fig_atr.update_layout(height=250, yaxis_title="ATR", margin=dict(l=40,r=20,t=30,b=40))
        st.plotly_chart(fig_atr, use_container_width=True)

    with c2:
        fig_mfi = pb("MFI")
        fig_mfi.add_trace(go.Scatter(x=hist.index, y=mfi_vals, name="MFI (14)",
            line=dict(color=C["blue"], width=1.6)))
        fig_mfi.add_hrect(y0=80, y1=100, fillcolor="rgba(255,77,109,0.08)", line_width=0)
        fig_mfi.add_hrect(y0=0,  y1=20,  fillcolor="rgba(0,255,224,0.08)", line_width=0)
        fig_mfi.add_hline(y=80, line_dash="dash", line_color=C["red"],  line_width=1)
        fig_mfi.add_hline(y=20, line_dash="dash", line_color=C["teal"], line_width=1)
        fig_mfi.update_layout(height=250, yaxis_title="MFI", yaxis_range=[0,100],
                               margin=dict(l=40,r=20,t=30,b=40))
        st.plotly_chart(fig_mfi, use_container_width=True)

    with st.expander("☁️ Ichimoku Cloud"):
        tenkan, kijun, senkou_a, senkou_b, chikou = ind.ichimoku(high, low, close)
        fig_ichi = pb("Ichimoku")
        fig_ichi.add_trace(go.Candlestick(
            x=hist.index, open=open_, high=high, low=low, close=close,
            increasing=dict(line=dict(color=C["teal"])),
            decreasing=dict(line=dict(color=C["red"])),
            name="OHLC", showlegend=False))
        fig_ichi.add_trace(go.Scatter(x=hist.index, y=tenkan, name="Tenkan",
            line=dict(color=C["red"], width=1.2)))
        fig_ichi.add_trace(go.Scatter(x=hist.index, y=kijun, name="Kijun",
            line=dict(color=C["blue"], width=1.2)))
        fig_ichi.add_trace(go.Scatter(x=hist.index, y=senkou_a, name="Senkou A",
            line=dict(color="rgba(0,255,224,0.5)", width=1), showlegend=False))
        fig_ichi.add_trace(go.Scatter(x=hist.index, y=senkou_b, name="Senkou B",
            line=dict(color="rgba(255,77,109,0.5)", width=1),
            fill="tonexty", fillcolor="rgba(168,85,247,0.06)", showlegend=False))
        fig_ichi.update_layout(**PLOTLY_BASE, height=400, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig_ichi, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 3 · ML FORECAST
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    sec("30-Day Multi-Model Forecast", "🤖")

    st.info(
        "📌 **Models**: LSTM (Deep Learning) · XGBoost · Gradient Boosting · Random Forest · **Ensemble**\n\n"
        "Forecasts are rolled forward day-by-day using lag/return/rolling features. "
        "Confidence band = ±1 annualised σ scaled by √t.",
        icon="ℹ️"
    )

    close_arr = close.values
    forecasts = {}
    metrics   = {}
    prog = st.progress(0, text="Training models…")

    for i, (name, key) in enumerate([("XGBoost","xgb"),("Gradient Boost","gbr"),("Random Forest","rf")]):
        prog.progress(int((i+1)/6*100), text=f"Training {name}…")
        m, X_te, y_te, y_pred_te = mdl.train_sklearn(close_arr, key)
        forecasts[name] = mdl.forecast_sklearn(m, close_arr, horizon)
        metrics[name]   = mdl.evaluate(y_te, y_pred_te)

    prog.progress(75, text="Training Ridge baseline…")
    m_r, X_te_r, y_te_r, y_pred_r = mdl.train_sklearn(close_arr, "ridge")
    forecasts["Ridge"] = mdl.forecast_sklearn(m_r, close_arr, horizon)
    metrics["Ridge"]   = mdl.evaluate(y_te_r, y_pred_r)

    lstm_model = None
    if use_lstm:
        prog.progress(85, text="Training LSTM (this may take ~30s)…")
        returns_arr = np.diff(close_arr) / close_arr[:-1]
        scaler = __import__("sklearn.preprocessing", fromlist=["MinMaxScaler"]).MinMaxScaler()
        scaled = scaler.fit_transform(returns_arr.reshape(-1,1)).flatten()
        lstm_model, X_te_l, y_te_l, y_pred_l, lb = mdl.train_lstm(scaled, look_back=60, epochs=25)
        if lstm_model is not None:
            lstm_fc = mdl.forecast_lstm(lstm_model, scaled, scaler, horizon, lb, close_arr[-1])
            min_len = min(len(lstm_fc), min(len(v) for v in forecasts.values()))
            for k in list(forecasts.keys()):
                forecasts[k] = forecasts[k][:min_len]
            forecasts["LSTM"]  = lstm_fc[:min_len]
            y_te_ret = scaler.inverse_transform(y_te_l.reshape(-1,1)).flatten()
            y_pr_ret = scaler.inverse_transform(y_pred_l.reshape(-1,1)).flatten()
            metrics["LSTM"]    = mdl.evaluate(y_te_ret, y_pr_ret)
        else:
            st.warning("TensorFlow not installed — LSTM skipped.")

    prog.progress(95, text="Building Ensemble…")
    weights = {k: max(0.01, v.get("Dir. Acc %",50)) for k, v in metrics.items()}
    ensemble_fc = mdl.ensemble_forecast(forecasts, weights)
    forecasts["⭐ Ensemble"] = ensemble_fc
    prog.progress(100, text="Done!"); prog.empty()

    n_fc = min(len(v) for v in forecasts.values())
    future_dates = pd.bdate_range(hist.index[-1] + timedelta(days=1), periods=n_fc)

    daily_std  = close.pct_change().std()
    t_arr      = np.arange(1, n_fc + 1)
    ens_fc     = forecasts["⭐ Ensemble"][:n_fc]
    conf_hi    = ens_fc * (1 + 1.65 * daily_std * np.sqrt(t_arr))
    conf_lo    = ens_fc * (1 - 1.65 * daily_std * np.sqrt(t_arr))

    fig_fc = pb("Forecast")
    lookback_plot = min(180, len(close))
    fig_fc.add_trace(go.Scatter(
        x=hist.index[-lookback_plot:], y=close.values[-lookback_plot:],
        name="Historical", line=dict(color=C["teal"], width=2),
    ))

    palette = [C["orange"], C["purple"], C["blue"], C["yellow"], C["green"]]
    for idx, (name, fc_vals) in enumerate(forecasts.items()):
        if name == "⭐ Ensemble": continue
        fig_fc.add_trace(go.Scatter(
            x=future_dates[:n_fc], y=fc_vals[:n_fc],
            name=name, mode="lines",
            line=dict(color=palette[idx % len(palette)], width=1.2, dash="dot"),
            opacity=0.65,
        ))

    fig_fc.add_trace(go.Scatter(
        x=future_dates, y=ens_fc,
        name="⭐ Ensemble", mode="lines+markers",
        line=dict(color="#ffffff", width=2.5),
        marker=dict(size=4, color="#ffffff"),
    ))
    fig_fc.add_trace(go.Scatter(
        x=list(future_dates) + list(future_dates[::-1]),
        y=list(conf_hi) + list(conf_lo[::-1]),
        fill="toself", fillcolor="rgba(255,255,255,0.06)",
        line=dict(color="rgba(0,0,0,0)"), name="90% CI",
    ))
    today_x = hist.index[-1]
    fig_fc.add_trace(go.Scatter(
        x=[today_x, today_x],
        y=[close.min() * 0.95, close.max() * 1.05],
        mode="lines",
        line=dict(color="rgba(255,255,255,0.25)", width=1.5, dash="dash"),
        name="Today", showlegend=False,
    ))
    fig_fc.update_layout(**PLOTLY_BASE, height=480,
                         yaxis_title=f"Price ({curr_code})",
                         title=dict(text=f"{ticker} · {n_fc}-Day Multi-Model Forecast",
                                    font=dict(family="'Syne',sans-serif", size=14)))
    st.plotly_chart(fig_fc, use_container_width=True)

    sec("30-Day Forecast Summary", "📋")
    fc_cols = st.columns(len(forecasts))
    for col, (name, fc_arr) in zip(fc_cols, forecasts.items()):
        fc_end   = fc_arr[min(n_fc-1, len(fc_arr)-1)]
        ret      = (fc_end / curr - 1) * 100
        val_clr  = "#00ffe0" if ret >= 0 else "#ff4d6d"
        with col:
            st.html(f"""<div class="metric-card" style="text-align:center">
              <div class="m-label" style="font-size:0.6rem">{name}</div>
              <div style="font-size:1.1rem;font-weight:600;color:{C['text']}">{c_sym}{fc_end:.2f}</div>
              <div class="m-sub" style="color:{val_clr}">{ret:+.1f}%</div>
            </div>""")

    sec("Model Accuracy Metrics (Test Set)", "🎯")
    rows = []
    for mname, met in metrics.items():
        rows.append({
            "Model": mname,
            "MAE (%)":   f"{met['MAE']*100:.4f}",
            "RMSE (%)":  f"{met['RMSE']*100:.4f}",
            "R²":        f"{met['R²']:.4f}",
            "MAPE (%)":  f"{met['MAPE %']:.2f}",
            "Dir. Acc (%)": f"{met['Dir. Acc %']:.1f}",
        })
    df_acc = pd.DataFrame(rows)
    st.dataframe(df_acc.set_index("Model"), use_container_width=True)

    with st.expander("📅 Full Forecast Table (Day-by-Day)"):
        df_fc_full = pd.DataFrame({"Date": future_dates.strftime("%Y-%m-%d")})
        for name, fc_arr in forecasts.items():
            df_fc_full[name] = [f"{c_sym}{v:.2f}" for v in fc_arr[:n_fc]]
        df_fc_full["CI Lower"] = [f"{c_sym}{v:.2f}" for v in conf_lo]
        df_fc_full["CI Upper"] = [f"{c_sym}{v:.2f}" for v in conf_hi]
        st.dataframe(df_fc_full.set_index("Date"), use_container_width=True)
        csv = df_fc_full.to_csv(index=False)
        st.download_button("⬇️ Download Forecast CSV", csv, f"{ticker}_forecast.csv", "text/csv")


# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 4 · RISK ANALYSIS
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    sec("Risk Metrics", "⚠️")
    rm = mdl.risk_metrics(close, rf_annual=rf_rate)

    r1, r2, r3, r4 = st.columns(4)
    def risk_card(col, lbl, val, fmt, good_positive=True):
        try:
            v = float(val)
            if good_positive: clr = C["teal"] if v >= 0 else C["red"]
            else:              clr = C["teal"] if v <= 0 else C["red"]
        except: clr = C["text"]; v = val
        with col:
            st.html(f"""<div class="metric-card">
              <div class="m-label">{lbl}</div>
              <div class="m-value" style="color:{clr};font-size:1.4rem">{fmt.format(v)}</div>
            </div>""")

    risk_card(r1, "Sharpe Ratio",   rm["Sharpe Ratio"],    "{:.3f}")
    risk_card(r2, "Sortino Ratio",  rm["Sortino Ratio"],   "{:.3f}")
    risk_card(r3, "Calmar Ratio",   rm["Calmar Ratio"],    "{:.3f}")
    risk_card(r4, "Ann. Return",    rm["Ann. Return"],     "{:.1f}%")

    r5, r6, r7, r8 = st.columns(4)
    risk_card(r5, "Ann. Volatility",  rm["Ann. Volatility"],   "{:.1f}%", False)
    risk_card(r6, "Max Drawdown",     rm["Max Drawdown"],      "{:.2f}%", False)
    risk_card(r7, "VaR 95% (Daily)",  rm["VaR 95%"],           "{:.2f}%", False)
    risk_card(r8, "CVaR 95% (Daily)", rm["CVaR 95%"],          "{:.2f}%", False)

    st.html("<div style='height:0.5rem'></div>")
    sec("Drawdown Over Time", "📉")
    roll_max = close.cummax()
    drawdown = (close - roll_max) / roll_max * 100

    fig_dd = pb("Drawdown")
    fig_dd.add_trace(go.Scatter(
        x=hist.index, y=drawdown,
        name="Drawdown", line=dict(color=C["red"], width=1.5),
        fill="tozeroy", fillcolor="rgba(255,77,109,0.1)",
    ))
    fig_dd.update_layout(**PLOTLY_BASE, height=280, yaxis_title="Drawdown (%)")
    st.plotly_chart(fig_dd, use_container_width=True)

    c_r1, c_r2 = st.columns(2)
    with c_r1:
        sec("Rolling Sharpe Ratio (252d)", "📈")
        daily_ret  = close.pct_change()
        roll_sharpe = (daily_ret.rolling(252).mean() / daily_ret.rolling(252).std()) * np.sqrt(252)
        fig_rs = pb("Rolling Sharpe")
        fig_rs.add_trace(go.Scatter(x=hist.index, y=roll_sharpe, name="Sharpe",
            line=dict(color=C["purple"], width=1.6)))
        fig_rs.add_hline(y=1, line_dash="dash", line_color=C["teal"], line_width=1)
        fig_rs.add_hline(y=0, line_dash="dot", line_color=C["text_dim"], line_width=0.8)
        fig_rs.update_layout(**PLOTLY_BASE, height=280, yaxis_title="Sharpe")
        st.plotly_chart(fig_rs, use_container_width=True)

    with c_r2:
        sec("Rolling Volatility (30d Ann.)", "📊")
        roll_vol = daily_ret.rolling(30).std() * np.sqrt(252) * 100
        fig_rv = pb("Rolling Vol")
        fig_rv.add_trace(go.Scatter(x=hist.index, y=roll_vol, name="Vol",
            line=dict(color=C["orange"], width=1.6),
            fill="tozeroy", fillcolor="rgba(249,115,22,0.07)"))
        fig_rv.update_layout(**PLOTLY_BASE, height=280, yaxis_title="Volatility (%)")
        st.plotly_chart(fig_rv, use_container_width=True)

    sec(f"Monte Carlo Simulation  ({mc_sims:,} paths · {horizon} days)", "🎲")
    with st.spinner("Running Monte Carlo…"):
        mc_paths = mdl.monte_carlo(close, n_days=horizon, n_sims=mc_sims)

    fig_mc = pb("Monte Carlo")
    sample_n = min(200, mc_sims)
    for i in range(sample_n):
        fig_mc.add_trace(go.Scatter(
            x=list(range(horizon + 1)), y=mc_paths[i],
            mode="lines", line=dict(color="rgba(168,85,247,0.06)", width=0.8),
            showlegend=False,
        ))
    p5  = np.percentile(mc_paths, 5,  axis=0)
    p25 = np.percentile(mc_paths, 25, axis=0)
    p50 = np.percentile(mc_paths, 50, axis=0)
    p75 = np.percentile(mc_paths, 75, axis=0)
    p95 = np.percentile(mc_paths, 95, axis=0)

    x_ax = list(range(horizon + 1))
    fig_mc.add_trace(go.Scatter(x=x_ax+x_ax[::-1], y=list(p95)+list(p5[::-1]),
        fill="toself", fillcolor="rgba(168,85,247,0.07)",
        line=dict(color="rgba(0,0,0,0)"), name="P5–P95"))
    fig_mc.add_trace(go.Scatter(x=x_ax+x_ax[::-1], y=list(p75)+list(p25[::-1]),
        fill="toself", fillcolor="rgba(168,85,247,0.15)",
        line=dict(color="rgba(0,0,0,0)"), name="P25–P75"))
    fig_mc.add_trace(go.Scatter(x=x_ax, y=p50, name="Median",
        line=dict(color=C["teal"], width=2.5)))
    fig_mc.add_trace(go.Scatter(x=x_ax, y=p5,  name="5th Pct",
        line=dict(color=C["red"],  width=1.5, dash="dash")))
    fig_mc.add_trace(go.Scatter(x=x_ax, y=p95, name="95th Pct",
        line=dict(color=C["green"],width=1.5, dash="dash")))

    fig_mc.update_layout(**PLOTLY_BASE, height=400,
                         xaxis_title=f"Days Ahead (from {hist.index[-1].strftime('%d %b %Y')})",
                         yaxis_title=f"Simulated Price ({curr_code})")
    st.plotly_chart(fig_mc, use_container_width=True)

    mc_cols = st.columns(5)
    mc_final = mc_paths[:, -1]
    mc_sum = [
        ("Median",   f"{c_sym}{np.median(mc_final):.2f}",      C["teal"]),
        ("P5 (Bear)",f"{c_sym}{np.percentile(mc_final,5):.2f}", C["red"]),
        ("P95 (Bull)",f"{c_sym}{np.percentile(mc_final,95):.2f}",C["green"]),
        ("Prob ↑",   f"{(mc_final > curr).mean()*100:.1f}%",C["teal"]),
        ("Prob ↓",   f"{(mc_final < curr).mean()*100:.1f}%",C["red"]),
    ]
    for col, (lbl, val, clr) in zip(mc_cols, mc_sum):
        with col:
            st.html(f"""<div class="metric-card" style="text-align:center">
              <div class="m-label">{lbl}</div>
              <div style="font-size:1.2rem;font-weight:600;color:{clr}">{val}</div>
            </div>""")

    sec("Value at Risk & CVaR Summary", "📊")
    fig_var = pb("VaR")
    var_labels = ["VaR 95%", "VaR 99%", "CVaR 95%", "CVaR 99%"]
    var_vals   = [rm["VaR 95%"], rm["VaR 99%"], rm["CVaR 95%"], rm["CVaR 99%"]]
    fig_var.add_trace(go.Bar(x=var_labels, y=var_vals,
        marker_color=[C["orange"], C["red"], C["purple"], "#ff0055"],
        text=[f"{v:.2f}%" for v in var_vals], textposition="outside",
        name="Risk %"))
    fig_var.update_layout(**PLOTLY_BASE, height=280, yaxis_title="Daily Loss (%)", bargap=0.4)
    st.plotly_chart(fig_var, use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 5 · COMPARISON
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    sec("Multi-Stock Comparison", "🔀")
    all_tickers = [ticker] + [t for t in compare_tickers if t != ticker]

    with st.spinner("Loading comparison data…"):
        comp_df = load_multi(all_tickers, period)

    if comp_df.empty:
        st.warning("No data loaded.")
    else:
        normed  = (comp_df / comp_df.iloc[0]) * 100
        palette = [C["teal"], C["orange"], C["purple"], C["blue"], C["red"], C["green"], C["yellow"]]

        fig_cmp = pb("Comparison")
        for i, col_name in enumerate(normed.columns):
            fig_cmp.add_trace(go.Scatter(
                x=normed.index, y=normed[col_name], mode="lines",
                name=col_name, line=dict(color=palette[i % len(palette)], width=2),
            ))
        fig_cmp.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.15)", line_width=1)
        fig_cmp.update_layout(**PLOTLY_BASE, height=420, yaxis_title="Normalised Return (Base=100)")
        st.plotly_chart(fig_cmp, use_container_width=True)

        c_col1, c_col2 = st.columns([1, 1])
        with c_col1:
            sec("Correlation Matrix", "🔗")
            corr = comp_df.pct_change().corr()
            fig_heat = go.Figure(go.Heatmap(
                z=corr.values, x=corr.columns, y=corr.index,
                colorscale=[[0,C["red"]],[0.5,"#1a1a3a"],[1,C["teal"]]],
                zmin=-1, zmax=1, text=np.round(corr.values, 2), texttemplate="%{text}", textfont=dict(size=11),
            ))
            fig_heat.update_layout(**{k:v for k,v in PLOTLY_BASE.items() if "axis" not in k and k != "margin"}, height=350, margin=dict(l=60,r=20,t=20,b=60))
            st.plotly_chart(fig_heat, use_container_width=True)

        with c_col2:
            sec("Return vs Risk Scatter", "⚖️")
            scatter_data = []
            for sym in comp_df.columns:
                s = comp_df[sym].dropna()
                ann_ret = s.pct_change().mean() * 252 * 100
                ann_vol_s = s.pct_change().std() * np.sqrt(252) * 100
                scatter_data.append({"Ticker": sym, "Ann Return %": ann_ret, "Ann Vol %": ann_vol_s})
            df_sc = pd.DataFrame(scatter_data)
            fig_sc = pb("Scatter")
            fig_sc.add_trace(go.Scatter(
                x=df_sc["Ann Vol %"], y=df_sc["Ann Return %"],
                mode="markers+text", text=df_sc["Ticker"], textposition="top center",
                marker=dict(size=14, color=palette[:len(df_sc)], line=dict(color="white", width=1)),
                name="Stocks",
            ))
            fig_sc.update_layout(**PLOTLY_BASE, height=350, xaxis_title="Annualised Volatility (%)", yaxis_title="Annualised Return (%)")
            st.plotly_chart(fig_sc, use_container_width=True)

        sec("Comparative Summary", "📋")
        rows = []
        for sym in comp_df.columns:
            s = comp_df[sym].dropna()
            r = (s.iloc[-1] / s.iloc[0] - 1) * 100
            v = s.pct_change().std() * np.sqrt(252) * 100
            sr = (s.pct_change().mean() - rf_rate/252) / s.pct_change().std() * np.sqrt(252)
            md = ((s / s.cummax()) - 1).min() * 100
            rows.append({"Ticker": sym, "Return %": f"{r:+.1f}%",
                         "Ann. Vol %": f"{v:.1f}%", "Sharpe": f"{sr:.2f}",
                         "Max DD %": f"{md:.1f}%",
                         "Period High": f"{c_sym}{s.max():.2f}",
                         "Period Low":  f"{c_sym}{s.min():.2f}"})
        st.dataframe(pd.DataFrame(rows).set_index("Ticker"), use_container_width=True)

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 6 · FUNDAMENTALS
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    sec("Fundamental Analysis", "📋")
    tk_obj = yf.Ticker(ticker)

    f1, f2 = st.columns([1, 1])
    with f1:
        ratios = [
            ("P/E Ratio",          info.get("trailingPE")),
            ("Forward P/E",        info.get("forwardPE")),
            ("PEG Ratio",          info.get("pegRatio")),
            ("Price/Book",         info.get("priceToBook")),
            ("EV/EBITDA",          info.get("enterpriseToEbitda")),
            ("EV/Revenue",         info.get("enterpriseToRevenue")),
            ("Profit Margin",      info.get("profitMargins")),
            ("Operating Margin",   info.get("operatingMargins")),
            ("Gross Margin",       info.get("grossMargins")),
            ("ROE",                info.get("returnOnEquity")),
            ("ROA",                info.get("returnOnAssets")),
            ("Debt/Equity",        info.get("debtToEquity")),
            ("Current Ratio",      info.get("currentRatio")),
            ("Quick Ratio",        info.get("quickRatio")),
        ]
        table_html = '<div style="background:rgba(14,14,36,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1rem;">'
        for k, v in ratios:
            if v is None: disp = "N/A"
            elif "Margin" in k or "ROE" in k or "ROA" in k: disp = f"{v*100:.2f}%"
            elif "Debt" in k: disp = f"{v:.1f}"
            else: disp = f"{v:.2f}"
            table_html += f'<div class="info-row"><span class="info-key">{k}</span><span class="info-val">{disp}</span></div>'
        table_html += "</div>"
        sec("Valuation & Profitability Ratios", "💰")
        st.html(table_html)

    with f2:
        sec("Financial Health Radar", "🕸️")
        radar_cats = ["Profitability", "Liquidity", "Valuation", "Growth", "Efficiency"]
        def norm(v, lo, hi): return max(0, min(1, (v-lo)/(hi-lo))) if v is not None else 0.3
        radar_vals = [
            norm((info.get("profitMargins") or 0)*100, -20, 40),
            norm(info.get("currentRatio") or 0, 0, 4),
            1 - norm(info.get("trailingPE") or 20, 5, 60),
            norm((info.get("revenueGrowth") or 0)*100, -10, 30),
            norm((info.get("returnOnEquity") or 0)*100, -10, 50),
        ]
        radar_fig = go.Figure(go.Scatterpolar(
            r=radar_vals + [radar_vals[0]], theta=radar_cats + [radar_cats[0]],
            fill="toself", name=ticker, line=dict(color=C["teal"], width=2), fillcolor="rgba(0,255,224,0.1)",
        ))
        radar_fig.update_layout(**{k:v for k,v in PLOTLY_BASE.items() if "axis" not in k and k != "hovermode"},
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, range=[0,1], gridcolor=C["grid"], tickfont=dict(color=C["text_dim"])),
                angularaxis=dict(gridcolor=C["grid"], tickfont=dict(color=C["text_mid"])),
            ), height=360, showlegend=False,
        )
        st.plotly_chart(radar_fig, use_container_width=True)

    try:
        inc = tk_obj.income_stmt
        if inc is not None and not inc.empty:
            sec("Income Statement (Annual)", "📊")
            cols_plot = ["Total Revenue", "Gross Profit", "Operating Income", "Net Income"]
            available = [c for c in cols_plot if c in inc.index]
            fig_inc = pb("Income")
            bar_colors = [C["teal"], C["blue"], C["orange"], C["purple"]]
            years = [str(d.year) for d in inc.columns]
            for i, row_name in enumerate(available):
                vals = inc.loc[row_name] / 1e9
                fig_inc.add_trace(go.Bar(
                    x=years, y=vals.values, name=row_name,
                    marker_color=bar_colors[i], marker_opacity=0.85,
                ))
            fig_inc.update_layout(**PLOTLY_BASE, height=320, barmode="group", yaxis_title=f"{c_sym} Billion", bargap=0.2, bargroupgap=0.05)
            st.plotly_chart(fig_inc, use_container_width=True)
    except: pass

    try:
        bs = tk_obj.balance_sheet
        if bs is not None and not bs.empty:
            sec("Balance Sheet (Annual)", "🏦")
            bs_rows = ["Total Assets", "Total Liabilities Net Minority Interest",
                       "Stockholders Equity", "Cash And Cash Equivalents"]
            avail_bs = [r for r in bs_rows if r in bs.index]
            fig_bs = pb("Balance Sheet")
            years_bs = [str(d.year) for d in bs.columns]
            bs_colors = [C["teal"], C["red"], C["green"], C["blue"]]
            for i, row_name in enumerate(avail_bs):
                vals = bs.loc[row_name] / 1e9
                fig_bs.add_trace(go.Bar(
                    x=years_bs, y=vals.values,
                    name=row_name.replace("Net Minority Interest","").strip(),
                    marker_color=bs_colors[i], marker_opacity=0.85,
                ))
            fig_bs.update_layout(**PLOTLY_BASE, height=300, barmode="group", yaxis_title=f"{c_sym} Billion", bargap=0.2)
            st.plotly_chart(fig_bs, use_container_width=True)
    except: pass

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 7 · BACKTESTING
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[6]:
    sec("Strategy Backtesting", "🎯")
    b1, b2 = st.columns(2)
    with b1:
        fast_ma = st.slider("Fast MA", 5, 50,  20)
        slow_ma = st.slider("Slow MA", 20, 200, 50)
    with b2:
        rsi_ov  = st.slider("RSI Oversold",   10, 40, 30)
        rsi_ob  = st.slider("RSI Overbought", 60, 90, 70)

    bt_ma  = mdl.backtest_ma_crossover(close, fast_ma, slow_ma)
    bt_rsi = mdl.backtest_rsi_strategy(close, rsi_ov, rsi_ob)

    sec(f"MA Crossover ({fast_ma}/{slow_ma}) vs Buy-&-Hold", "📈")
    fig_bt1 = pb("MA Backtest")
    fig_bt1.add_trace(go.Scatter(x=bt_ma["dates"], y=bt_ma["bh_cum"]*100-100, name="Buy & Hold", line=dict(color=C["text_dim"], width=1.8, dash="dash")))
    fig_bt1.add_trace(go.Scatter(x=bt_ma["dates"], y=bt_ma["strat_cum"]*100-100, name=f"MA {fast_ma}/{slow_ma}", line=dict(color=C["teal"], width=2)))
    fig_bt1.add_hline(y=0, line_dash="dot", line_color=C["text_dim"], line_width=0.8)
    fig_bt1.update_layout(**PLOTLY_BASE, height=320, yaxis_title="Cumulative Return (%)")
    st.plotly_chart(fig_bt1, use_container_width=True)

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    for col, lbl, val, clr in [(mc1, "Strategy Return", f"{bt_ma['strat_total']*100:+.1f}%", pct_color(bt_ma['strat_total'])),
                               (mc2, "B&H Return",      f"{bt_ma['bh_total']*100:+.1f}%", pct_color(bt_ma['bh_total'])),
                               (mc3, "Alpha",           f"{(bt_ma['strat_total']-bt_ma['bh_total'])*100:+.1f}%", pct_color(bt_ma['strat_total']-bt_ma['bh_total'])),
                               (mc4, "Strat Sharpe",    f"{bt_ma['strat_sharpe']:.2f}", C["purple"]),
                               (mc5, "# Trades",        str(bt_ma['num_trades']),       C["text_dim"])]:
        with col:
            st.html(f"""<div class="metric-card" style="text-align:center"><div class="m-label">{lbl}</div><div style="font-size:1.1rem;font-weight:600;color:{clr}">{val}</div></div>""")

    sec(f"RSI Strategy (OB={rsi_ob}, OS={rsi_ov}) vs Buy-&-Hold", "📊")
    fig_bt2 = pb("RSI Backtest")
    fig_bt2.add_trace(go.Scatter(x=bt_rsi["dates"], y=bt_rsi["bh_cum"]*100-100, name="Buy & Hold", line=dict(color=C["text_dim"], width=1.8, dash="dash")))
    fig_bt2.add_trace(go.Scatter(x=bt_rsi["dates"], y=bt_rsi["strat_cum"]*100-100, name=f"RSI Strategy", line=dict(color=C["orange"], width=2)))
    fig_bt2.add_hline(y=0, line_dash="dot", line_color=C["text_dim"], line_width=0.8)
    fig_bt2.update_layout(**PLOTLY_BASE, height=320, yaxis_title="Cumulative Return (%)")
    st.plotly_chart(fig_bt2, use_container_width=True)

    rc1, rc2, rc3, rc4, rc5 = st.columns(5)
    for col, lbl, val, clr in [(rc1, "Strategy Return", f"{bt_rsi['strat_total']*100:+.1f}%", pct_color(bt_rsi['strat_total'])),
                               (rc2, "B&H Return",      f"{bt_rsi['bh_total']*100:+.1f}%", pct_color(bt_rsi['bh_total'])),
                               (rc3, "Alpha",           f"{(bt_rsi['strat_total']-bt_rsi['bh_total'])*100:+.1f}%", pct_color(bt_rsi['strat_total']-bt_rsi['bh_total'])),
                               (rc4, "Strat Sharpe",    f"{bt_rsi['strat_sharpe']:.2f}", C["purple"]),
                               (rc5, "# Trades",        str(bt_rsi['num_trades']),       C["text_dim"])]:
        with col:
            st.html(f"""<div class="metric-card" style="text-align:center"><div class="m-label">{lbl}</div><div style="font-size:1.1rem;font-weight:600;color:{clr}">{val}</div></div>""")

    sec("Monthly Return Heatmap", "🗓️")
    try:
        monthly = close.resample("M").last().pct_change().dropna() * 100
        monthly_df = monthly.reset_index()
        monthly_df.columns = ["Date","Return"]
        monthly_df["Year"]  = monthly_df["Date"].dt.year
        monthly_df["Month"] = monthly_df["Date"].dt.strftime("%b")
        pivot = monthly_df.pivot_table(index="Year", columns="Month", values="Return", aggfunc="mean")
        month_order = ["Jan","Feb","Mar","Apr","May","Jun", "Jul","Aug","Sep","Oct","Nov","Dec"]
        pivot = pivot.reindex(columns=[m for m in month_order if m in pivot.columns])
        fig_mh = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
            colorscale=[[0,C["red"]],[0.5,"#0e0e24"],[1,C["teal"]]], zmid=0,
            text=np.round(pivot.values, 1), texttemplate="%{text}%", textfont=dict(size=10),
        ))
        fig_mh.update_layout(**{k:v for k,v in PLOTLY_BASE.items() if "axis" not in k and k != "margin"}, height=350, margin=dict(l=60,r=20,t=20,b=40), xaxis=dict(side="bottom"), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_mh, use_container_width=True)
    except Exception as e:
        st.caption(f"Monthly heatmap unavailable: {e}")

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 8 · NEWS & SENTIMENT
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[7]:
    sec("News & Sentiment Analysis", "📰")

    try:
        from textblob import TextBlob
        news_list = yf.Ticker(ticker).news[:20] or []
    except Exception:
        news_list = []

    if not news_list:
        st.info("No recent news. Ensure `textblob` is installed: `pip install textblob`")
    else:
        records = []
        for item in news_list:
            c_item = item.get("content", item)
            title = c_item.get("title") or ""
            summary = c_item.get("summary") or c_item.get("description") or ""
            source = (c_item.get("provider") or {}).get("displayName") or item.get("publisher") or "Unknown"
            url = (c_item.get("canonicalUrl") or {}).get("url") or item.get("link") or ""
            raw_date = c_item.get("pubDate") or c_item.get("displayTime")
            if raw_date:
                try:
                    date_str = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).strftime("%d %b %Y %H:%M")
                except Exception:
                    date_str = str(raw_date)
            elif item.get("providerPublishTime"):
                date_str = datetime.fromtimestamp(item["providerPublishTime"]).strftime("%d %b %Y %H:%M")
            else:
                date_str = ""
            if not title:
                continue
            blob = TextBlob(f"{title}. {summary}")
            score = blob.sentiment.polarity
            lbl = "Bullish" if score > 0.05 else ("Bearish" if score < -0.05 else "Neutral")
            records.append({
                "title": title, "summary": summary, "source": source, "url": url,
                "date": date_str, "image": c_item.get("thumbnail") or item.get("thumbnail") or {},
                "score": score, "subjectivity": blob.sentiment.subjectivity, "lbl": lbl,
            })

        for r in records:
            c1, c2 = st.columns([1, 4])

            with c1:
                try:
                    img = r["image"]["resolutions"][0]["url"]
                    st.image(img, width=120)
                except Exception:
                    pass

            with c2:
                st.markdown(f"### {r['title']}")
                st.caption(f"{r['source']} • {r['date']}")
                st.write(r["summary"])

                if r["lbl"] == "Bullish":
                    st.success("🟢 Bullish")
                elif r["lbl"] == "Bearish":
                    st.error("🔴 Bearish")
                else:
                    st.warning("🟡 Neutral")

                if r["url"]:
                    st.link_button("Read Full Article", r["url"])

            st.divider()

        sec("Overall Sentiment", "🎯")
        avg_score = np.mean([r["score"] for r in records]) if records else 0.0
        g1, g2 = st.columns([1, 2])

        with g1:
            gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta", value=avg_score, delta={"reference": 0, "valueformat": ".3f"},
                title={"text": "Avg Sentiment", "font": {"color": C["text_dim"], "size": 13}},
                number={"font": {"size": 30, "color": C["text"]}, "valueformat": ".3f"},
                gauge={
                    "axis": {"range": [-1, 1], "tickcolor": C["text_dim"]},
                    "bar": {"color": C["teal"] if avg_score > 0 else C["red"], "thickness": 0.25},
                    "bgcolor": "rgba(0,0,0,0)", "bordercolor": C["grid"],
                    "steps": [{"range": [-1,  -0.05], "color": "rgba(255,77,109,0.12)"},
                              {"range": [-0.05,0.05], "color": "rgba(251,191,36,0.08)"},
                              {"range": [0.05,  1],   "color": "rgba(0,255,224,0.12)"}],
                },
            ))
            gauge.update_layout(**{k:v for k,v in PLOTLY_BASE.items() if "axis" not in k and k not in ("hovermode","margin")}, height=240, margin=dict(l=20,r=20,t=30,b=10))
            st.plotly_chart(gauge, use_container_width=True)

        with g2:
            df_news = pd.DataFrame(records)
            fig_news_sc = pb("Sentiment Scatter")
            colors_s = [C["teal"] if s > 0.05 else (C["red"] if s < -0.05 else C["yellow"]) for s in df_news["score"]]
            fig_news_sc.add_trace(go.Scatter(
                x=df_news["subjectivity"], y=df_news["score"], mode="markers+text",
                text=[t[:30]+"…" for t in df_news["title"]], textposition="top center", textfont=dict(size=7, color=C["text_dim"]),
                marker=dict(size=10, color=colors_s, line=dict(color="rgba(255,255,255,0.2)", width=1)), name="Articles",
            ))
            fig_news_sc.add_hline(y=0,    line_dash="dot", line_color=C["text_dim"])
            fig_news_sc.add_vline(x=0.5,  line_dash="dot", line_color=C["text_dim"])
            fig_news_sc.update_layout(**PLOTLY_BASE, height=240, xaxis_title="Subjectivity", yaxis_title="Polarity")
            st.plotly_chart(fig_news_sc, use_container_width=True)

        bull = sum(1 for r in records if r["lbl"] == "Bullish")
        bear = sum(1 for r in records if r["lbl"] == "Bearish")
        neut = sum(1 for r in records if r["lbl"] == "Neutral")
        sn1, sn2, sn3 = st.columns(3)
        for col, lbl, cnt, clr in [(sn1,"Bullish Articles",bull,C["teal"]),
                                    (sn2,"Bearish Articles",bear,C["red"]),
                                    (sn3,"Neutral Articles",neut,C["yellow"])]:
            with col:
                st.html(f"""<div class="metric-card" style="text-align:center"><div class="m-label">{lbl}</div><div style="font-size:2rem;font-weight:700;color:{clr}">{cnt}</div></div>""")

# ╔══════════════════════════════════════════════════════════════════════════════
# TAB 9 · Wishlist & Price Alerts
# ╚══════════════════════════════════════════════════════════════════════════════
with tabs[8]:
    if sl_current_user:
        sl_wish.render_wishlist_dashboard(st.session_state.get("uid", ""), C)
    else:
        st.info("🔐 Sign in with Google to use the Wishlist & Price Alerts feature.")
        st.markdown(
            "Set target prices and stop-loss levels for any stock. "
            "The StockLens Pro notification service will email you the moment a condition is met."
        )

# ═══════════════════
st.html(f"""
<div class="footer">
  StockLens Pro · Built with Streamlit · Data via Yahoo Finance ·
  ML: XGBoost · Gradient Boosting · Random Forest · LSTM (TensorFlow) ·
  Sentiment: TextBlob · Risk: NumPy/SciPy ·
  Last refresh {datetime.now().strftime('%H:%M:%S %Z')}
</div>""")