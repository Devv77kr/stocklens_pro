# auth.py  ── StockLens Pro · Google OAuth via streamlit-google-auth

import streamlit as st
import json
import os

# ── Try importing streamlit_google_auth ───────────────────────────────────────
try:
    from streamlit_google_auth import Authenticate
    _AUTH_AVAILABLE = True
except ImportError:
    _AUTH_AVAILABLE = False


def _get_authenticator():
    """Build the Authenticate object from st.secrets."""
    if not _AUTH_AVAILABLE:
        return None
    try:
        secrets = st.secrets.get("google_oauth", {})
        client_id     = secrets.get("client_id", "")
        client_secret = secrets.get("client_secret", "")
        redirect_uri  = secrets.get("redirect_uri", "http://localhost:8501")
        if not client_id or not client_secret:
            return None
        return Authenticate(
            secret_credentials_path=None,
            cookie_name="stocklens_auth",
            cookie_key="stocklens_secret_key_2024",
            redirect_uri=redirect_uri,
            client_id=client_id,
            client_secret=client_secret,
        )
    except Exception:
        return None


def get_current_user() -> dict | None:
    """
    Returns the signed-in user dict: {name, email, picture}
    or None if not signed in.
    Uses st.session_state so it persists across reruns.
    """
    return st.session_state.get("sl_user", None)


def logout():
    """Clear the logged-in user from session."""
    if "sl_user" in st.session_state:
        del st.session_state["sl_user"]
    if "sl_auth_obj" in st.session_state:
        try:
            st.session_state["sl_auth_obj"].logout()
        except Exception:
            pass
        del st.session_state["sl_auth_obj"]
    st.rerun()


def render_auth_panel(C: dict):
    """
    Render the auth panel inside the Streamlit sidebar.
    Shows:
      - Google Sign-In button (when not logged in)
      - User avatar + name + logout (when logged in)
    Returns the current user dict or None.
    """
    user = get_current_user()

    if user:
        # ── Signed-in state ─────────────────────────────────────────────────
        pic   = user.get("picture", "")
        name  = user.get("name", "User")
        email = user.get("email", "")

        avatar_html = (f'<img src="{pic}" class="user-avatar">' if pic else "👤")
        st.sidebar.markdown(
            f"""<div class="auth-panel">
                {avatar_html}
                <div class="auth-greeting">👋 Hi, {name.split()[0]}!</div>
                <div class="auth-email">{email}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.sidebar.button("🚪 Sign Out", use_container_width=True, key="sl_signout"):
            logout()
        return user

    else:
        # ── Signed-out state ─────────────────────────────────────────────────
        st.sidebar.markdown(
            f"""<div class="auth-panel">
                <div class="auth-greeting">🔐 Sign in to unlock</div>
                <div class="auth-email" style="margin-bottom:10px">
                  Watchlist · Smart Alerts · Personalised UI
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        if not _AUTH_AVAILABLE:
            st.sidebar.warning(
                "Install: `pip install streamlit-google-auth`",
                icon="⚠️",
            )
            # ── Demo mode: allow manual name entry for testing ───────────────
            with st.sidebar.expander("🧪 Demo Login (no OAuth)"):
                demo_name  = st.text_input("Your Name",  key="demo_name")
                demo_email = st.text_input("Your Email", key="demo_email")
                if st.button("Enter as Demo User", key="demo_login"):
                    if demo_name and demo_email:
                        st.session_state["sl_user"] = {
                            "name":    demo_name,
                            "email":   demo_email,
                            "picture": "",
                        }
                        st.rerun()
            return None

        # ── Real Google OAuth ────────────────────────────────────────────────
        auth = _get_authenticator()
        if auth is None:
            st.sidebar.error(
                "Google OAuth not configured.\n\n"
                "Add credentials to `.streamlit/secrets.toml`",
                icon="🔑",
            )
            return None

        st.session_state["sl_auth_obj"] = auth
        auth.check_authentification()

        if auth.is_logged_in():
            user_info = {
                "name":    auth.get_user_info().get("name", "User"),
                "email":   auth.get_user_info().get("email", ""),
                "picture": auth.get_user_info().get("picture", ""),
            }
            st.session_state["sl_user"] = user_info
            st.rerun()
        else:
            auth.login()

        return None
