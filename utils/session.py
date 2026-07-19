# utils/session.py

from typing import Optional
import streamlit as st
from utils.constants import SESSION_KEYS


def set_user_session(uid: str, name: str, email: str, photo_url: str, user_dict: dict):
    st.session_state["authenticated"] = True
    st.session_state["uid"]           = uid
    st.session_state["name"]          = name
    st.session_state["email"]         = email
    st.session_state["photo_url"]     = photo_url
    st.session_state["user"]          = user_dict
    # Legacy key consumed by watchlist/alerts render functions
    st.session_state["sl_user"] = {
        "name":    name,
        "email":   email,
        "picture": photo_url,
    }


def clear_session():
    for k in SESSION_KEYS + ["sl_user", "sl_auth_obj"]:
        st.session_state.pop(k, None)


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated", False))


def get_current_user() -> Optional[dict]:
    if not is_authenticated():
        return None
    return st.session_state.get("user")
