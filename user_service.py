# user_service.py ── User profile CRUD in Firestore

from typing import Optional
from datetime import datetime, timezone
from firebase_service import get_db, firebase_available

try:
    from firebase_admin import firestore as fb_firestore
    SERVER_TS = fb_firestore.SERVER_TIMESTAMP
except ImportError:
    SERVER_TS = None


def _server_ts():
    return SERVER_TS if SERVER_TS is not None else datetime.now(timezone.utc).isoformat()


def save_user_to_firestore(
    uid: str,
    name: str,
    email: str,
    photo_url: str,
    provider: str = "google",
) -> Optional[dict]:
    """
    Create user doc on first login; update last_login + display info on subsequent logins.
    Returns the user dict (from Firestore or locally constructed).
    """
    db = get_db()
    if db is None:
        return _local_user_dict(uid, name, email, photo_url, provider)

    try:
        ref = db.collection("users").document(uid)
        doc = ref.get()
        if doc.exists:
            ref.update({
                "last_login":    _server_ts(),
                "display_name":  name,
                "photo_url":     photo_url,
            })
            data = doc.to_dict()
            data.update({"display_name": name, "photo_url": photo_url})
            return data
        else:
            data = {
                "uid":             uid,
                "display_name":    name,
                "email":           email,
                "photo_url":       photo_url,
                "provider":        provider,
                "created_at":      _server_ts(),
                "last_login":      _server_ts(),
                "watchlist_count": 0,
                "alerts_count":    0,
            }
            ref.set(data)
            return data
    except Exception:
        return _local_user_dict(uid, name, email, photo_url, provider)


def load_user_data(uid: str) -> Optional[dict]:
    """Fetch user doc from Firestore by uid."""
    db = get_db()
    if db is None:
        return None
    try:
        doc = db.collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        return None


def update_watchlist_count(uid: str, count: int):
    db = get_db()
    if db is None:
        return
    try:
        db.collection("users").document(uid).update({"watchlist_count": count})
    except Exception:
        pass


def update_alerts_count(uid: str, count: int):
    db = get_db()
    if db is None:
        return
    try:
        db.collection("users").document(uid).update({"alerts_count": count})
    except Exception:
        pass


def _local_user_dict(uid, name, email, photo_url, provider):
    """Fallback user dict when Firestore is unavailable."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "uid":             uid,
        "display_name":    name,
        "email":           email,
        "photo_url":       photo_url,
        "provider":        provider,
        "created_at":      now,
        "last_login":      now,
        "watchlist_count": 0,
        "alerts_count":    0,
    }
