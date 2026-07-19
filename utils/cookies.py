# utils/cookies.py

import json
from typing import Optional
from utils.constants import COOKIE_NAME, COOKIE_EXPIRY_DAYS

try:
    import extra_streamlit_components as stx
    _COOKIES_AVAILABLE = True
except ImportError:
    _COOKIES_AVAILABLE = False


def get_cookie_manager():
    if not _COOKIES_AVAILABLE:
        return None
    return stx.CookieManager(key="stocklens_cookie_mgr")


def save_session_cookie(cookie_manager, uid: str, name: str, email: str, photo_url: str):
    if cookie_manager is None:
        return
    try:
        payload = json.dumps({
            "uid":       uid,
            "name":      name,
            "email":     email,
            "photo_url": photo_url,
        })
        cookie_manager.set(
            COOKIE_NAME,
            payload,
            max_age=COOKIE_EXPIRY_DAYS * 86400,
        )
    except Exception:
        pass


def load_session_cookie(cookie_manager) -> Optional[dict]:
    if cookie_manager is None:
        return None
    try:
        raw = cookie_manager.get(COOKIE_NAME)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def clear_session_cookie(cookie_manager):
    if cookie_manager is None:
        return
    try:
        cookie_manager.delete(COOKIE_NAME)
    except Exception:
        pass
