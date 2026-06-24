# auth.py ── StockLens Pro · Google OAuth2 + Firebase Admin + Firestore
# Uses raw HTTP (requests) for OAuth — bypasses google_auth_oauthlib.flow.Flow
# to avoid PKCE code_verifier being lost across Streamlit's redirect boundary.

import urllib.parse
import requests
import streamlit as st
from typing import Optional

from firebase_service import initialize_firebase, get_or_create_firebase_user
from user_service import save_user_to_firestore, load_user_data
from utils.session import set_user_session, clear_session, is_authenticated, get_current_user
from utils.cookies import save_session_cookie, load_session_cookie, clear_session_cookie

_SCOPES = " ".join([
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
])

_GOOGLE_AUTH_URI  = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"

_GOOGLE_BUTTON_SVG = (
    '<svg width="18" height="18" viewBox="0 0 24 24" style="flex-shrink:0">'
    '<path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92'
    'c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>'
    '<path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77'
    'c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84'
    'C3.99 20.53 7.7 23 12 23z"/>'
    '<path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43'
    '.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>'
    '<path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15'
    'C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84'
    'c.87-2.6 3.3-4.53 6.16-4.53z"/>'
    '</svg>'
)


# ── Public API ────────────────────────────────────────────────────────────────

def initialize_firebase_auth():
    initialize_firebase()


def handle_oauth_callback(cookie_manager) -> bool:
    """
    Call once per app load (before any render).
    Detects Google's ?code= redirect, exchanges it for tokens, creates Firebase
    user, sets session + cookie, clears query params.

    Returns True only on a fresh successful login.
    Guards against double-exchange: stores the processed code in session_state.
    Caller must NOT call st.rerun() after this — st.query_params.clear()
    already schedules a rerun and a second rerun causes invalid_grant.
    """
    params = st.query_params
    if "code" not in params:
        return False

    code = params.get("code", "")
    if not code:
        return False

    # Guard 1: already authenticated (cookie restore ran first or page refresh)
    if is_authenticated():
        st.query_params.clear()
        return False

    # Guard 2: we already exchanged this exact code in a prior run of this script
    # (happens when st.query_params.clear() triggers a rerun before URL updates in browser)
    if st.session_state.get("_oauth_code_done") == code:
        st.query_params.clear()
        return False

    # Mark as in-progress immediately to prevent any concurrent re-entry
    st.session_state["_oauth_code_done"] = code

    try:
        info  = _exchange_code(code)

        name  = info.get("name", "User")
        email = info.get("email", "")
        photo = info.get("picture", "")

        if not email:
            st.error("Google sign-in did not return an email address.")
            st.query_params.clear()
            return False

        uid      = get_or_create_firebase_user(email, name, photo)
        user_doc = save_user_to_firestore(uid, name, email, photo)
        set_user_session(uid, name, email, photo, user_doc)
        save_session_cookie(cookie_manager, uid, name, email, photo)
        st.query_params.clear()   # triggers a natural rerun — caller must NOT also call st.rerun()
        return True

    except Exception as e:
        err = str(e)
        if "invalid_grant" in err:
            st.error(
                "🔐 Sign-in link already used or expired — please click **Sign in with Google** again.",
                icon="⚠️",
            )
        else:
            st.error(f"Sign-in failed: {e}")
        st.query_params.clear()
        return False


def restore_session_from_cookie(cookie_manager):
    """Restore session from cookie on each page load if not already authenticated."""
    if is_authenticated():
        return
    data = load_session_cookie(cookie_manager)
    if not data:
        return
    uid = data.get("uid")
    if not uid:
        return
    user_doc = load_user_data(uid)
    if user_doc:
        set_user_session(
            uid,
            user_doc.get("display_name", data.get("name", "User")),
            user_doc.get("email",        data.get("email", "")),
            user_doc.get("photo_url",    data.get("photo_url", "")),
            user_doc,
        )
    else:
        set_user_session(uid, data.get("name", "User"), data.get("email", ""),
                         data.get("photo_url", ""), data)


def maybe_save_cookie(cookie_manager):
    """
    Call after CookieManager is initialized.
    Saves session cookie if the user is authenticated but no cookie has been
    written yet this session (e.g. first login, or cookie was skipped during
    the pre-CookieManager OAuth callback phase).
    """
    if not is_authenticated():
        return
    if cookie_manager is None:
        return
    if st.session_state.get("_cookie_saved"):
        return
    uid   = st.session_state.get("uid", "")
    name  = st.session_state.get("name", "")
    email = st.session_state.get("email", "")
    photo = st.session_state.get("photo_url", "")
    if uid:
        save_session_cookie(cookie_manager, uid, name, email, photo)
        st.session_state["_cookie_saved"] = True


def logout(cookie_manager=None):
    clear_session()
    st.session_state.pop("_cookie_saved", None)
    st.session_state.pop("_oauth_code_done", None)
    if cookie_manager is not None:
        clear_session_cookie(cookie_manager)
    st.rerun()


def google_login(cookie_manager):
    """Render 'Sign in with Google' button in current Streamlit context."""
    try:
        auth_url = _build_auth_url()
    except Exception as e:
        st.error(f"OAuth not configured: {e}", icon="🔑")
        return

    st.markdown(
        f"""<a href="{auth_url}" target="_self" style="text-decoration:none;">
          <div class="google-signin-btn">
            {_GOOGLE_BUTTON_SVG}
            <span>Sign in with Google</span>
          </div>
        </a>""",
        unsafe_allow_html=True,
    )


def is_user_authenticated() -> bool:
    return is_authenticated()


def save_user_to_firestore_fn(uid, name, email, photo_url, provider="google"):
    return save_user_to_firestore(uid, name, email, photo_url, provider)


def load_user_data_fn(uid):
    return load_user_data(uid)


# ── Render helpers ────────────────────────────────────────────────────────────

def render_auth_button(C: dict) -> str:
    """
    HTML for topbar auth zone.
    Signed in  → <details> dropdown: avatar + name trigger, profile info + logout.
    Signed out → Google Sign-In link.
    Logout uses ?action=logout link — detected in app.py startup.
    """
    if is_authenticated():
        user  = st.session_state.get("user", {})
        name  = user.get("display_name", st.session_state.get("name", "User"))
        email = user.get("email",        st.session_state.get("email", ""))
        photo = st.session_state.get("photo_url", "")
        first = name.split()[0]
        avatar_sm = (
            f'<img src="{photo}" class="user-avatar" alt="{first}">'
            if photo else '<span style="font-size:1.1rem;line-height:1">👤</span>'
        )
        avatar_lg = (
            f'<img src="{photo}" class="dropdown-avatar" alt="{name}">'
            if photo else '<span class="dropdown-avatar-placeholder">👤</span>'
        )
        teal = C.get("teal", "#00ffe0")
        return f"""
<details class="topbar-user-menu">
  <summary class="topbar-user-trigger" style="--accent:{teal}">
    {avatar_sm}
    <span class="topbar-username" style="color:{teal}">{first}</span>
    <span class="topbar-chevron">▾</span>
  </summary>
  <div class="topbar-dropdown">
    <div class="dropdown-profile-row">
      {avatar_lg}
      <div class="dropdown-profile-text">
        <div class="dropdown-name">{name}</div>
        <div class="dropdown-email">{email}</div>
      </div>
    </div>
    <div class="dropdown-divider"></div>
    <a href="?action=logout" target="_self" class="dropdown-logout-link">
      🚪&nbsp; Sign Out
    </a>
  </div>
</details>"""
    else:
        try:
            auth_url = _build_auth_url()
            return (
                f'<a href="{auth_url}" target="_self" style="text-decoration:none;">'
                f'<div class="google-signin-topbar">'
                f'{_GOOGLE_BUTTON_SVG}'
                f'<span style="font-size:0.72rem;margin-left:6px;">Sign in with Google</span>'
                f'</div></a>'
            )
        except Exception:
            return '<span style="font-size:0.72rem;color:#64748b;">Sign in unavailable</span>'


def render_user_profile(C: dict):
    user     = st.session_state.get("user", {})
    name     = user.get("display_name", st.session_state.get("name", "User"))
    email    = user.get("email",        st.session_state.get("email", ""))
    photo    = user.get("photo_url",    st.session_state.get("photo_url", ""))
    created  = user.get("created_at",   "")
    wl_count = user.get("watchlist_count", 0)
    al_count = user.get("alerts_count",    0)

    try:
        join_str = str(created)[:10] if created else "—"
    except Exception:
        join_str = "—"

    avatar_html = (
        f'<img src="{photo}" class="profile-avatar" alt="{name}">'
        if photo else
        '<div class="profile-avatar-placeholder">👤</div>'
    )

    st.sidebar.markdown(
        f"""<div class="profile-card">
            <div class="profile-avatar-wrap">{avatar_html}</div>
            <div class="profile-name">{name}</div>
            <div class="profile-email">{email}</div>
            <div class="profile-stats">
              <div class="profile-stat">
                <div class="stat-val">{wl_count}</div>
                <div class="stat-lbl">Watchlist</div>
              </div>
              <div class="profile-stat-div"></div>
              <div class="profile-stat">
                <div class="stat-val">{al_count}</div>
                <div class="stat-lbl">Alerts</div>
              </div>
              <div class="profile-stat-div"></div>
              <div class="profile-stat">
                <div class="stat-val" style="font-size:0.65rem">{join_str}</div>
                <div class="stat-lbl">Joined</div>
              </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_logout_button(cookie_manager=None):
    if st.sidebar.button("🚪 Sign Out", use_container_width=True, key="sl_signout_btn"):
        logout(cookie_manager)


def render_auth_panel(C: dict, cookie_manager=None):
    """
    Sidebar auth panel.
    Signed in → profile card + logout.
    Signed out → Google Sign-In button.
    Returns current user dict or None.
    """
    user = get_current_user()

    if user:
        render_user_profile(C)
        render_logout_button(cookie_manager)
        return user

    st.sidebar.markdown(
        """<div class="auth-panel">
            <div class="auth-greeting">🔐 Sign in to unlock</div>
            <div class="auth-email" style="margin-bottom:12px">
              Watchlist · Smart Alerts · Personalised UI
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.sidebar:
        google_login(cookie_manager)

    return None


# ── Internal helpers (raw HTTP — no google_auth_oauthlib.Flow, no PKCE) ──────

def _oauth_secrets():
    s = st.secrets.get("google_oauth", {})
    cid = s.get("client_id", "")
    csec = s.get("client_secret", "")
    ruri = s.get("redirect_uri", "http://localhost:8501")
    if not cid or not csec:
        raise ValueError("google_oauth credentials missing in secrets.toml")
    return cid, csec, ruri


def _build_auth_url() -> str:
    """Build Google OAuth2 authorization URL using urllib — zero PKCE, zero state loss."""
    client_id, _, redirect_uri = _oauth_secrets()
    params = urllib.parse.urlencode({
        "client_id":     client_id,
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         _SCOPES,
        "access_type":   "offline",
        "prompt":        "select_account",
    })
    return f"{_GOOGLE_AUTH_URI}?{params}"


def _exchange_code(code: str) -> Optional[dict]:
    """
    Exchange authorization code for tokens via direct HTTP POST.
    Returns user-info dict {name, email, picture} or None on failure.
    """
    client_id, client_secret, redirect_uri = _oauth_secrets()

    # Step 1: exchange code for access token
    token_resp = requests.post(
        _GOOGLE_TOKEN_URI,
        data={
            "code":          code,
            "client_id":     client_id,
            "client_secret": client_secret,
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code",
        },
        timeout=10,
    )
    token_resp.raise_for_status()
    token_data   = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError(f"No access_token in response: {token_data}")

    # Step 2: fetch user profile
    info_resp = requests.get(
        _GOOGLE_USERINFO,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    info_resp.raise_for_status()
    return info_resp.json()
