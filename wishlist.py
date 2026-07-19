# wishlist.py ── StockLens Pro · Wishlist & Price Alert UI

import streamlit as st
import yfinance as yf

import watchlist_service as wl_svc


# ── currency helper ───────────────────────────────────────────────────────────

@st.cache_data(ttl=60, show_spinner=False)
def _get_current_price(symbol: str) -> tuple[float, str]:
    """Fetch live price + currency symbol for a ticker."""
    try:
        info = yf.Ticker(symbol).fast_info
        price = float(info.last_price or 0)
        currency = getattr(info, "currency", "USD")
        sym = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, currency + " ")
        return price, sym
    except Exception:
        return 0.0, "$"


def _fmt(sym: str, price: float) -> str:
    return f"{sym}{price:,.2f}"


# ── Add to Wishlist modal ─────────────────────────────────────────────────────

@st.dialog("⭐ Add to Wishlist")
def render_add_to_wishlist_modal(
    uid: str,
    ticker: str,
    company_name: str,
    current_price: float,
    c_sym: str,
    C: dict,
):
    existing = wl_svc.get_alert_by_symbol(uid, ticker)
    editing  = existing is not None

    st.markdown(
        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;'
        f'color:{C.get("text_dim","#94a3b8")};margin-bottom:0.5rem;">'
        f'{"Update alert for" if editing else "Set price targets for"} '
        f'<span style="color:{C.get("teal","#00ffe0")};font-weight:700;">{ticker}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div style="font-size:1.5rem;font-weight:700;font-family:\'IBM Plex Mono\',monospace;'
        f'margin-bottom:1rem;">'
        f'Current Price: <span style="color:{C.get("teal","#00ffe0")}">'
        f'{_fmt(c_sym, current_price)}</span></div>',
        unsafe_allow_html=True,
    )

    default_target = existing.get("target_price", round(current_price * 1.10, 2)) if editing else round(current_price * 1.10, 2)
    default_stop   = existing.get("stop_loss",   round(current_price * 0.90, 2)) if editing else round(current_price * 0.90, 2)
    default_notif  = existing.get("notification_enabled", True) if editing else True

    target = st.number_input(
        f"🎯 Target Price ({c_sym})",
        min_value=0.01,
        value=float(default_target),
        step=0.5,
        help=f"Must be above {_fmt(c_sym, current_price)}",
    )
    stop = st.number_input(
        f"🛡️ Stop Loss ({c_sym})",
        min_value=0.01,
        value=float(default_stop),
        step=0.5,
        help=f"Must be below {_fmt(c_sym, current_price)}",
    )
    notif = st.toggle("🔔 Enable Email Notifications", value=default_notif)

    err = None
    if target <= current_price:
        err = f"Target must be above current price ({_fmt(c_sym, current_price)})"
    elif stop >= current_price:
        err = f"Stop Loss must be below current price ({_fmt(c_sym, current_price)})"
    elif stop >= target:
        err = "Stop Loss must be below Target Price"

    if err:
        st.error(err)

    col1, col2 = st.columns(2)
    with col1:
        save_clicked = st.button(
            "💾 Update Alert" if editing else "⭐ Save Alert",
            use_container_width=True,
            type="primary",
            disabled=bool(err),
        )
    with col2:
        if st.button("✕ Cancel", use_container_width=True):
            st.session_state.pop("open_wish_modal", None)
            st.rerun()

    if save_clicked and not err:
        if editing:
            ok = wl_svc.update_alert(uid, existing["alert_id"], target, stop, notif)
        else:
            ok = wl_svc.create_alert(uid, ticker, company_name, current_price, target, stop, notif)
        if ok:
            st.session_state.pop("open_wish_modal", None)
            st.toast(f"✅ Alert {'updated' if editing else 'saved'} for {ticker}!", icon="⭐")
            st.rerun()
        else:
            st.error("Failed to save — check Firebase connection.")


# ── Wishlist dashboard tab ────────────────────────────────────────────────────

def render_wishlist_dashboard(uid: str, C: dict):
    st.html('<div class="sec-title">⭐ WISHLIST &amp; PRICE ALERTS</div>')

    alerts = wl_svc.get_alerts(uid)

    if not alerts:
        st.markdown(
            '<div style="text-align:center;padding:3rem 0;font-family:\'IBM Plex Mono\',monospace;'
            'font-size:0.9rem;color:var(--dim);">'
            '⭐ No price alerts yet.<br><br>'
            'Search a stock above and click the <strong>☆</strong> button to add one.</div>',
            unsafe_allow_html=True,
        )
        return

    # ── Summary row ──────────────────────────────────────────────────────────
    total      = len(alerts)
    active     = sum(1 for a in alerts if a.get("notification_enabled") and not (a.get("target_triggered") or a.get("stop_triggered")))
    triggered  = sum(1 for a in alerts if a.get("target_triggered") or a.get("stop_triggered"))
    disabled   = sum(1 for a in alerts if not a.get("notification_enabled"))

    teal   = C.get("teal",   "#00ffe0")
    green  = C.get("green",  "#4ade80")
    red    = C.get("red",    "#ff4d6d")
    purple = C.get("purple", "#a855f7")
    text   = C.get("text",   "#e2e8f0")
    dim    = C.get("text_dim","#64748b")

    m1, m2, m3, m4 = st.columns(4)
    for col, lbl, val, clr in [
        (m1, "Total Alerts",   total,     text),
        (m2, "Active",         active,    teal),
        (m3, "Triggered",      triggered, green),
        (m4, "Disabled",       disabled,  purple),
    ]:
        with col:
            st.html(f"""
            <div class="metric-card">
              <div class="m-label">{lbl}</div>
              <div class="m-value" style="color:{clr}">{val}</div>
            </div>""")

    st.html("<div style='height:0.5rem'></div>")

    # ── Per-alert cards ───────────────────────────────────────────────────────
    for alert in alerts:
        _render_alert_card(uid, alert, C)


def _render_alert_card(uid: str, alert: dict, C: dict):
    alert_id  = alert["alert_id"]
    symbol    = alert.get("stock_symbol", "")
    company   = alert.get("company_name", symbol)
    target    = alert.get("target_price", 0.0)
    stop      = alert.get("stop_loss", 0.0)
    notif     = alert.get("notification_enabled", True)
    t_trig    = alert.get("target_triggered", False)
    s_trig    = alert.get("stop_triggered", False)
    stored_px = alert.get("current_price", 0.0)

    teal   = C.get("teal",   "#00ffe0")
    green  = C.get("green",  "#4ade80")
    red    = C.get("red",    "#ff4d6d")
    purple = C.get("purple", "#a855f7")
    text   = C.get("text",   "#e2e8f0")
    dim    = C.get("text_dim","#64748b")

    # Live price fetch (cached by Streamlit's st.cache_data in app.py — here we do a quick yf call)
    curr_px, c_sym = _get_current_price(symbol)
    if curr_px == 0.0:
        curr_px = stored_px
        c_sym   = "₹" if symbol.endswith(".NS") or symbol.endswith(".BO") else "$"

    # Status badge
    if not notif:
        badge_col, badge_txt = purple, "DISABLED"
    elif t_trig:
        badge_col, badge_txt = green,  "TARGET HIT ✓"
    elif s_trig:
        badge_col, badge_txt = red,    "STOP HIT ✗"
    else:
        badge_col, badge_txt = teal,   "ACTIVE"

    # Progress bar towards target (clamp 0–100%)
    rng  = target - stop if target > stop else 1
    prog = max(0.0, min(1.0, (curr_px - stop) / rng)) if rng > 0 else 0.0
    prog_pct = int(prog * 100)
    bar_filled = "█" * int(prog_pct / 5)
    bar_empty  = "░" * (20 - len(bar_filled))

    card_key = f"wish_card_{alert_id}"

    st.html(f"""
    <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;
                padding:1.2rem 1.4rem;margin-bottom:0.8rem;
                box-shadow:0 4px 20px rgba(0,0,0,0.15);">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">
        <div>
          <span style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;color:{text};">
            ⭐ {symbol}
          </span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:0.72rem;
                       color:{dim};margin-left:0.6rem;">{company}</span>
        </div>
        <span style="background:{badge_col}22;color:{badge_col};border:1px solid {badge_col}55;
                     border-radius:20px;padding:3px 12px;font-size:0.72rem;font-weight:700;
                     font-family:'IBM Plex Mono',monospace;">{badge_txt}</span>
      </div>

      <div style="display:flex;gap:1.5rem;margin-top:0.9rem;flex-wrap:wrap;
                  font-family:'IBM Plex Mono',monospace;font-size:0.82rem;">
        <div>
          <span style="color:{dim}">Current</span>&nbsp;
          <span style="color:{text};font-weight:700;">{_fmt(c_sym, curr_px)}</span>
        </div>
        <div>
          <span style="color:{dim}">Target</span>&nbsp;
          <span style="color:{green};font-weight:700;">{_fmt(c_sym, target)}</span>
        </div>
        <div>
          <span style="color:{dim}">Stop Loss</span>&nbsp;
          <span style="color:{red};font-weight:700;">{_fmt(c_sym, stop)}</span>
        </div>
      </div>

      <div style="margin-top:0.75rem;font-family:'IBM Plex Mono',monospace;font-size:0.72rem;color:{dim};">
        Progress to target &nbsp;
        <span style="color:{teal}">{bar_filled}</span><span style="color:var(--grid)">{bar_empty}</span>
        &nbsp;<span style="color:{text}">{prog_pct}%</span>
      </div>
    </div>""")

    # Action buttons
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 4])

    with btn_col1:
        if st.button("✏️ Edit", key=f"edit_{alert_id}", use_container_width=True):
            st.session_state[f"editing_{alert_id}"] = not st.session_state.get(f"editing_{alert_id}", False)

    with btn_col2:
        notif_icon = "🔕 Disable" if notif else "🔔 Enable"
        if st.button(notif_icon, key=f"notif_{alert_id}", use_container_width=True):
            wl_svc.toggle_notification(uid, alert_id, not notif)
            st.rerun()

    with btn_col3:
        if st.button("🗑️ Delete", key=f"del_{alert_id}", use_container_width=True):
            st.session_state[f"confirm_del_{alert_id}"] = True

    # Confirm delete
    if st.session_state.get(f"confirm_del_{alert_id}"):
        st.warning(f"Delete alert for **{symbol}**?")
        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button("Yes, delete", key=f"del_yes_{alert_id}", type="primary"):
                wl_svc.delete_alert(uid, alert_id)
                st.session_state.pop(f"confirm_del_{alert_id}", None)
                st.rerun()
        with dc2:
            if st.button("Cancel", key=f"del_no_{alert_id}"):
                st.session_state.pop(f"confirm_del_{alert_id}", None)
                st.rerun()

    # Inline edit form
    if st.session_state.get(f"editing_{alert_id}"):
        with st.container(border=True):
            st.markdown(f"**Edit alert for {symbol}**")
            new_target = st.number_input(
                f"Target ({c_sym})", value=float(target), step=0.5,
                key=f"ne_target_{alert_id}"
            )
            new_stop = st.number_input(
                f"Stop Loss ({c_sym})", value=float(stop), step=0.5,
                key=f"ne_stop_{alert_id}"
            )
            new_notif = st.toggle("Notifications", value=notif, key=f"ne_notif_{alert_id}")

            edit_err = None
            if new_target <= curr_px:
                edit_err = f"Target must be above current price ({_fmt(c_sym, curr_px)})"
            elif new_stop >= curr_px:
                edit_err = f"Stop Loss must be below current price ({_fmt(c_sym, curr_px)})"
            elif new_stop >= new_target:
                edit_err = "Stop Loss must be below Target Price"
            if edit_err:
                st.error(edit_err)

            ec1, ec2 = st.columns(2)
            with ec1:
                if st.button("💾 Save", key=f"save_edit_{alert_id}",
                             type="primary", disabled=bool(edit_err)):
                    ok = wl_svc.update_alert(uid, alert_id, new_target, new_stop, new_notif)
                    if ok:
                        st.session_state.pop(f"editing_{alert_id}", None)
                        st.toast(f"✅ {symbol} alert updated!", icon="⭐")
                        st.rerun()
                    else:
                        st.error("Save failed.")
            with ec2:
                if st.button("✕ Cancel", key=f"cancel_edit_{alert_id}"):
                    st.session_state.pop(f"editing_{alert_id}", None)
                    st.rerun()

    st.html("<div style='height:0.25rem'></div>")
