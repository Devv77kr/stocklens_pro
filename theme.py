# theme.py ── Centralised design tokens & CSS injection with Light/Dark support

def get_theme(mode="dark"):
    is_dark = mode == "dark"
    
    COLORS = {
        "bg":        "#080818" if is_dark else "#f8fafc",
        "bg2":       "#0e0e24" if is_dark else "#f1f5f9",
        "card":      "rgba(14,14,36,0.9)" if is_dark else "rgba(255,255,255,0.95)",
        "teal":      "#00ffe0" if is_dark else "#0d9488",
        "teal_dim":  "rgba(0,255,224,0.15)" if is_dark else "rgba(13,148,136,0.15)",
        "purple":    "#a855f7" if is_dark else "#7e22ce",
        "purple_dim":"rgba(168,85,247,0.15)" if is_dark else "rgba(126,34,206,0.15)",
        "orange":    "#632080" if is_dark else "#0c4fea",
        "orange_dim":"rgba(249,115,22,0.15)" if is_dark else "rgba(234,88,12,0.15)",
        "red":       "#ff4d6d" if is_dark else "#e11d48",
        "red_dim":   "rgba(255,77,109,0.15)" if is_dark else "rgba(225,29,72,0.15)",
        "blue":      "#38bdf8" if is_dark else "#0284c7",
        "green":     "#4ade80" if is_dark else "#16a34a",
        "yellow":    "#fbbf24" if is_dark else "#d97706",
        "grid":      "rgba(255,255,255,0.05)" if is_dark else "rgba(0,0,0,0.06)",
        "border":    "rgba(0,255,224,0.1)" if is_dark else "rgba(0,0,0,0.1)",
        "text":      "#e2e2f0" if is_dark else "#0f172a",
        "text_dim":  "#6e6e9a" if is_dark else "#64748b",
        "text_mid":  "#a0a0c0" if is_dark else "#475569",
    }

    PLOTLY_BASE = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor ="rgba(0,0,0,0)",
        font=dict(family="'IBM Plex Mono', monospace", color=COLORS["text"], size=11),
        xaxis=dict(gridcolor=COLORS["grid"], zeroline=False, showline=False, tickfont=dict(color=COLORS["text_dim"])),
        yaxis=dict(gridcolor=COLORS["grid"], zeroline=False, showline=False, tickfont=dict(color=COLORS["text_dim"])),
        hovermode="x unified",
        hoverlabel=dict(bgcolor=COLORS["bg2"], bordercolor=COLORS["teal"], font=dict(family="'IBM Plex Mono', monospace", color=COLORS["text"], size=11)),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"], borderwidth=1, font=dict(size=10), orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    )

    CSS = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Syne:wght@400;600;700;800&display=swap');

    :root {{
      --teal: {COLORS['teal']}; --purple: {COLORS['purple']}; --orange: {COLORS['orange']};
      --red: {COLORS['red']}; --blue: {COLORS['blue']}; --green: {COLORS['green']};
      --bg: {COLORS['bg']}; --bg2: {COLORS['bg2']}; --text: {COLORS['text']};
      --dim: {COLORS['text_dim']}; --card: {COLORS['card']}; --border: {COLORS['border']};
      --grid: {COLORS['grid']};
    }}

    html, body, [class*="css"] {{ font-family: 'IBM Plex Mono', monospace !important; background: var(--bg) !important; color: var(--text) !important; }}
    .stApp {{ background: radial-gradient(ellipse at 20% 10%, {COLORS['purple_dim']} 0%, transparent 50%), radial-gradient(ellipse at 80% 90%, {COLORS['teal_dim']} 0%, transparent 50%), var(--bg) !important; }}
    .block-container, .stMainBlockContainer {{ padding: 0 1.5rem 3rem 1.5rem !important; max-width: 100% !important; }}
    #MainMenu, footer {{ visibility: hidden !important; }}
    header {{ display: none !important; }}

    .topbar {{ background: {COLORS['bg2']}; border-bottom: 1px solid var(--border); padding: 0.75rem 2rem; margin: 0 -1.5rem 2rem -1.5rem; display: flex; align-items: center; justify-content: space-between; backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 999; }}
    .logo {{ font-family: 'Syne', sans-serif; font-size: 1.4rem; font-weight: 800; letter-spacing: -1px; color: var(--teal); }}
    .logo em {{ color: var(--purple); font-style: normal; }}
    .topbar-right {{ display:flex; gap:1rem; align-items:center; font-size:0.7rem; color:var(--dim); }}
    .live-dot {{ width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 8px var(--green); animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:0.4}} }}

    .topbar-nav {{ display:flex; gap:0.5rem; align-items:center; }}
    .topbar-nav-btn {{ background:transparent; border:1px solid var(--border); color:var(--dim); padding:4px 14px; border-radius:20px; font-size:0.68rem; font-family:'IBM Plex Mono',monospace; letter-spacing:0.08em; cursor:pointer; transition:all 0.2s; }}
    .topbar-nav-btn:hover {{ border-color:var(--teal); color:var(--teal); }}

    .sec-title {{ font-family: 'Syne', sans-serif; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: var(--teal); margin: 1.5rem 0 1rem 0; display: flex; align-items: center; gap: 0.6rem; }}
    .sec-title::after {{ content:''; flex:1; height:1px; background: linear-gradient(to right, {COLORS['teal_dim']}, transparent); }}

    .metric-card {{ background: var(--card); border: 1px solid var(--grid); border-radius: 12px; padding: 1.1rem 1.3rem; transition: all 0.25s ease; position: relative; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.02); }}
    .metric-card:hover {{ border-color: var(--border); transform: translateY(-3px); }}
    .m-label {{ font-size:0.65rem; color:var(--dim); letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.4rem; }}
    .m-value {{ font-size:1.6rem; font-weight:600; color:var(--text); line-height:1; }}
    .m-sub {{ font-size:0.68rem; margin-top:0.35rem; }}

    .info-row {{ display:flex; justify-content:space-between; align-items:center; padding: 0.5rem 0; border-bottom: 1px solid var(--grid); font-size: 0.78rem; }}
    .info-row:last-child {{ border-bottom: none; }}
    .info-key {{ color: var(--dim); }} .info-val {{ color: var(--text); font-weight: 500; }}

    .badge {{ display:inline-block; padding:2px 8px; border-radius:5px; font-size:0.65rem; font-weight:600; letter-spacing:0.05em; }}
    .badge-bull {{ background:{COLORS['teal_dim']}; color:var(--teal); border:1px solid var(--border); }}
    .badge-bear {{ background:{COLORS['red_dim']}; color:var(--red);  border:1px solid var(--border); }}
    .badge-neu  {{ background:{COLORS['orange_dim']}; color:var(--yellow);border:1px solid var(--border); }}

    .signal-row {{ display:flex; flex-wrap:wrap; gap:0.5rem; margin:0.5rem 0 1rem 0; }}
    .signal {{ padding:4px 12px; border-radius:20px; font-size:0.68rem; font-family:'Syne',sans-serif; font-weight:600; letter-spacing:0.04em; }}
    .sig-buy   {{ background:{COLORS['green']}; color:white; border:1px solid var(--border); opacity: 0.9; }}
    .sig-sell  {{ background:{COLORS['red']}; color:white;   border:1px solid var(--border); opacity: 0.9; }}
    .sig-hold  {{ background:{COLORS['yellow']}; color:white; border:1px solid var(--border); opacity: 0.9; }}

    .stTabs [data-baseweb="tab-list"] {{ background: var(--card) !important; border: 1px solid var(--grid) !important; border-radius: 12px !important; padding: 5px !important; gap: 4px !important; }}
    .stTabs [data-baseweb="tab"] {{ color: var(--dim) !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; font-size: 0.78rem !important; font-weight: 600 !important; padding: 6px 16px !important; }}
    .stTabs [aria-selected="true"] {{ background: linear-gradient(135deg, var(--purple), {COLORS['blue']}) !important; color: white !important; }}

    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div, .stMultiSelect > div > div {{ background: var(--bg2) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; color: var(--text) !important; font-family: 'IBM Plex Mono', monospace !important; }}
    .stSlider > div > div > div {{ background: var(--purple) !important; }}
    .streamlit-expanderHeader {{ background: var(--card) !important; border: 1px solid var(--grid) !important; border-radius: 8px !important; font-family: 'Syne', sans-serif !important; font-size: 0.8rem !important; font-weight: 600 !important; color:var(--text) !important; }}
    .footer {{ text-align:center; padding:1.5rem; margin-top:2rem; border-top:1px solid var(--grid); font-size:0.65rem; color:var(--dim); }}

    /* ── 3D Watchlist Cards ─────────────────────────────────────────────── */
    .wl-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        margin-top: 10px;
        perspective: 800px;
    }}
    .wl-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px 10px;
        text-align: center;
        transition: all 0.35s cubic-bezier(.25,.8,.25,1);
        transform: translateZ(0);
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
        cursor: pointer;
    }}
    .wl-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 2px;
        border-radius: 12px 12px 0 0;
    }}
    .wl-card:hover {{
        transform: translateY(-4px) translateZ(20px) rotateX(4deg);
        box-shadow: 0 12px 32px rgba(0,0,0,0.4);
    }}
    .wl-card-up::before  {{ background: linear-gradient(90deg, #22c55e, #00ffe0); }}
    .wl-card-down::before{{ background: linear-gradient(90deg, #ff4d6d, #f97316); }}
    .wl-card-up   {{ border-color: rgba(34,197,94,0.35); }}
    .wl-card-down {{ border-color: rgba(255,77,109,0.35); }}
    .wl-card-up:hover   {{ box-shadow: 0 12px 32px rgba(34,197,94,0.2); }}
    .wl-card-down:hover {{ box-shadow: 0 12px 32px rgba(255,77,109,0.2); }}
    .wl-ticker {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        color: var(--dim);
        letter-spacing: 1px;
        margin-bottom: 4px;
    }}
    .wl-price {{
        font-family: 'Syne', sans-serif;
        font-size: 1.0rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1.1;
    }}
    .wl-chg {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        font-weight: 600;
        margin-top: 3px;
    }}
    .wl-dir {{
        font-size: 1.1rem;
        margin-top: 2px;
    }}
    /* ── Heart Button ───────────────────────────────────────────────────── */
    .heart-btn {{
        background: none;
        border: none;
        font-size: 1.4rem;
        cursor: pointer;
        transition: transform 0.2s ease;
        display: inline-block;
        line-height: 1;
    }}
    .heart-btn:hover {{ transform: scale(1.3); }}
    .heart-btn.active {{ animation: heartbeat 0.4s ease; }}
    @keyframes heartbeat {{
        0%  {{ transform: scale(1); }}
        30% {{ transform: scale(1.5); }}
        60% {{ transform: scale(0.9); }}
        100%{{ transform: scale(1); }}
    }}
    /* ── Auth Panel ─────────────────────────────────────────────────────── */
    .auth-panel {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px 14px;
        text-align: center;
        margin-bottom: 12px;
    }}
    .auth-greeting {{
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.88rem;
        color: var(--text);
        margin-bottom: 4px;
    }}
    .auth-email {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.65rem;
        color: var(--dim);
    }}
    .user-avatar {{
        width: 32px; height: 32px;
        border-radius: 50%;
        border: 2px solid var(--teal);
        vertical-align: middle;
        margin-right: 6px;
    }}
    /* ── Alert Status ───────────────────────────────────────────────────── */
    .alert-sent {{
        background: rgba(34,197,94,0.08);
        border: 1px solid rgba(34,197,94,0.3);
        border-radius: 8px;
        padding: 8px 12px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        color: #22c55e;
        margin-top: 8px;
        text-align: center;
    }}
    /* ── Profile Card ───────────────────────────────────────────────────── */
    .profile-card {{
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 18px 14px 14px;
        text-align: center;
        margin-bottom: 12px;
        position: relative;
        overflow: hidden;
    }}
    .profile-card::before {{
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, {COLORS['teal']}, {COLORS['purple']});
    }}
    .profile-avatar-wrap {{
        margin-bottom: 10px;
    }}
    .profile-avatar {{
        width: 56px; height: 56px;
        border-radius: 50%;
        border: 2px solid {COLORS['teal']};
        box-shadow: 0 0 16px rgba(0,255,224,0.25);
        display: block;
        margin: 0 auto;
    }}
    .profile-avatar-placeholder {{
        width: 56px; height: 56px;
        border-radius: 50%;
        border: 2px solid {COLORS['teal']};
        background: var(--bg2);
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto;
        font-size: 1.6rem;
    }}
    .profile-name {{
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.92rem;
        color: var(--text);
        margin-bottom: 3px;
    }}
    .profile-email {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.62rem;
        color: var(--dim);
        margin-bottom: 12px;
        word-break: break-all;
    }}
    .profile-stats {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        border-top: 1px solid var(--grid);
        padding-top: 10px;
    }}
    .profile-stat {{
        flex: 1;
        text-align: center;
    }}
    .profile-stat-div {{
        width: 1px;
        height: 28px;
        background: var(--grid);
    }}
    .stat-val {{
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        color: {COLORS['teal']};
        line-height: 1.1;
    }}
    .stat-lbl {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.58rem;
        color: var(--dim);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
    }}
    /* ── Google Sign-In topbar button ───────────────────────────────────── */
    .google-signin-topbar {{
        display: flex;
        align-items: center;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 5px 14px;
        cursor: pointer;
        font-size: 0.72rem;
        color: var(--text);
        gap: 6px;
        transition: all 0.2s ease;
        text-decoration: none;
    }}
    .google-signin-topbar:hover {{
        background: rgba(255,255,255,0.1);
        border-color: {COLORS['teal']};
        color: {COLORS['teal']};
    }}
    /* ── Topbar user dropdown ───────────────────────────────────────────── */
    .topbar-user-menu {{
        position: relative;
        list-style: none;
    }}
    .topbar-user-trigger {{
        display: flex;
        align-items: center;
        gap: 7px;
        cursor: pointer;
        padding: 4px 10px;
        border-radius: 20px;
        border: 1px solid transparent;
        transition: border-color 0.2s, background 0.2s;
        user-select: none;
        outline: none;
    }}
    .topbar-user-trigger::-webkit-details-marker {{ display: none; }}
    .topbar-user-trigger::marker {{ display: none; }}
    .topbar-user-menu[open] .topbar-user-trigger,
    .topbar-user-trigger:hover {{
        background: rgba(0,255,224,0.06);
        border-color: rgba(0,255,224,0.25);
    }}
    .topbar-username {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
        font-weight: 500;
    }}
    .topbar-chevron {{
        font-size: 0.6rem;
        color: var(--dim);
        transition: transform 0.2s;
    }}
    .topbar-user-menu[open] .topbar-chevron {{
        transform: rotate(180deg);
    }}
    .topbar-dropdown {{
        position: absolute;
        right: 0;
        top: calc(100% + 8px);
        min-width: 220px;
        background: {COLORS['bg2']};
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.45);
        padding: 12px;
        z-index: 9999;
        backdrop-filter: blur(20px);
        animation: dropIn 0.15s ease;
    }}
    @keyframes dropIn {{
        from {{ opacity:0; transform:translateY(-6px); }}
        to   {{ opacity:1; transform:translateY(0); }}
    }}
    .dropdown-profile-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 4px 2px 8px 2px;
    }}
    .dropdown-avatar {{
        width: 40px; height: 40px;
        border-radius: 50%;
        border: 2px solid {COLORS['teal']};
        flex-shrink: 0;
    }}
    .dropdown-avatar-placeholder {{
        width: 40px; height: 40px;
        border-radius: 50%;
        background: var(--bg2);
        border: 2px solid {COLORS['teal']};
        display: flex; align-items: center; justify-content: center;
        font-size: 1.2rem; flex-shrink: 0;
    }}
    .dropdown-profile-text {{
        min-width: 0;
    }}
    .dropdown-name {{
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        font-size: 0.85rem;
        color: var(--text);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .dropdown-email {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.62rem;
        color: var(--dim);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .dropdown-divider {{
        height: 1px;
        background: var(--grid);
        margin: 8px 0;
    }}
    .dropdown-logout-link {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 8px;
        font-family: 'Syne', sans-serif;
        font-size: 0.8rem;
        font-weight: 600;
        color: {COLORS['red']};
        text-decoration: none;
        transition: background 0.15s;
    }}
    .dropdown-logout-link:hover {{
        background: {COLORS['red_dim']};
    }}
    /* ── Topbar user badge (legacy fallback) ────────────────────────────── */
    .topbar-user {{
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    /* ── Sidebar Google Sign-In button ──────────────────────────────────── */
    .google-signin-btn {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        background: white;
        color: #3c4043;
        border: 1px solid #dadce0;
        border-radius: 24px;
        padding: 10px 18px;
        font-family: 'Syne', sans-serif;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        width: 100%;
        margin: 4px 0;
    }}
    .google-signin-btn:hover {{
        background: #f8f9fa;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    </style>
    """
    return COLORS, PLOTLY_BASE, CSS