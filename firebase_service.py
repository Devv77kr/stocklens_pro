# firebase_service.py ── Firebase Admin SDK init + Firestore client

import json
import hashlib
import streamlit as st

try:
    import firebase_admin
    from firebase_admin import credentials, auth as fb_auth, firestore
    _FIREBASE_AVAILABLE = True
except ImportError:
    _FIREBASE_AVAILABLE = False

_db = None
_firebase_ok = False


@st.cache_resource(show_spinner=False)
def _create_firestore_client():
    """Create one Admin SDK client per Streamlit process."""
    if not _FIREBASE_AVAILABLE:
        return None
    if not firebase_admin._apps:
        sa_raw = st.secrets.get("firebase", {}).get("service_account_json", "")
        if not sa_raw:
            return None
        sa_dict = json.loads(sa_raw) if isinstance(sa_raw, str) else dict(sa_raw)
        firebase_admin.initialize_app(credentials.Certificate(sa_dict))
    return firestore.client()


def initialize_firebase() -> bool:
    """
    Initialize Firebase Admin SDK from secrets.toml service account JSON.
    Safe to call multiple times — skips if already initialised.
    Returns True on success.
    """
    global _db, _firebase_ok
    if not _FIREBASE_AVAILABLE:
        return False
    try:
        _db = _create_firestore_client()
        _firebase_ok = _db is not None
        return _firebase_ok
    except Exception as e:
        st.warning(f"Firebase init failed — running without Firestore. ({e})", icon="⚠️")
        return False


def get_db():
    """Return Firestore client, initialising Firebase if needed."""
    global _db
    if _db is None:
        initialize_firebase()
    return _db


def firebase_available() -> bool:
    return _FIREBASE_AVAILABLE and _firebase_ok


# ── Firebase Auth helpers ─────────────────────────────────────────────────────

def get_or_create_firebase_user(email: str, name: str, photo_url: str) -> str:
    """
    Look up or create a Firebase Auth user by email.
    Returns the Firebase uid string.
    Falls back to a deterministic sha256-based uid if Admin SDK unavailable.
    """
    if not _FIREBASE_AVAILABLE or not firebase_admin._apps:
        return _email_to_uid(email)
    try:
        user = fb_auth.get_user_by_email(email)
        # Keep display_name + photo in sync
        fb_auth.update_user(
            user.uid,
            display_name=name,
            photo_url=photo_url or None,
        )
        return user.uid
    except fb_auth.UserNotFoundError:
        new_user = fb_auth.create_user(
            email=email,
            display_name=name,
            photo_url=photo_url or None,
        )
        return new_user.uid
    except Exception:
        return _email_to_uid(email)


def _email_to_uid(email: str) -> str:
    """Deterministic 28-char uid fallback from email."""
    return hashlib.sha256(email.lower().encode()).hexdigest()[:28]
