# watchlist_service.py ── StockLens Pro · Price Alert CRUD (Firestore)

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from firebase_service import get_db

try:
    from firebase_admin import firestore as fb_firestore
    _FS_AVAILABLE = True
except ImportError:
    _FS_AVAILABLE = False

_TS = lambda: fb_firestore.SERVER_TIMESTAMP if _FS_AVAILABLE else None


# ── helpers ───────────────────────────────────────────────────────────────────

def _stocks_ref(uid: str):
    db = get_db()
    if db is None:
        return None
    return db.collection("price_alerts").document(uid).collection("stocks")


def _history_ref(uid: str):
    db = get_db()
    if db is None:
        return None
    return db.collection("alert_history").document(uid).collection("logs")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_alerts(uid: str) -> list[dict]:
    """Return all price-alert docs for uid, each with alert_id injected."""
    ref = _stocks_ref(uid)
    if ref is None:
        return []
    try:
        docs = ref.order_by("created_at", direction="DESCENDING").stream()
        results = []
        for d in docs:
            row = d.to_dict()
            row["alert_id"] = d.id
            results.append(row)
        return results
    except Exception:
        return []


def get_alert_by_symbol(uid: str, symbol: str) -> Optional[dict]:
    """Return first alert doc matching symbol, or None."""
    ref = _stocks_ref(uid)
    if ref is None:
        return None
    try:
        docs = list(ref.where("stock_symbol", "==", symbol.upper()).limit(1).stream())
        if docs:
            row = docs[0].to_dict()
            row["alert_id"] = docs[0].id
            return row
    except Exception:
        pass
    return None


def is_in_wishlist(uid: str, symbol: str) -> bool:
    return get_alert_by_symbol(uid, symbol.upper()) is not None


def create_alert(
    uid: str,
    stock_symbol: str,
    company_name: str,
    current_price: float,
    target_price: float,
    stop_loss: float,
    notification_enabled: bool = True,
) -> Optional[str]:
    """
    Create or replace alert for stock_symbol.
    If alert already exists for symbol, updates it instead.
    Returns alert_id or None on failure.
    """
    ref = _stocks_ref(uid)
    if ref is None:
        return None
    try:
        existing = get_alert_by_symbol(uid, stock_symbol)
        payload = {
            "stock_symbol":        stock_symbol.upper(),
            "company_name":        company_name,
            "current_price":       float(current_price),
            "target_price":        float(target_price),
            "stop_loss":           float(stop_loss),
            "notification_enabled": notification_enabled,
            "target_triggered":    False,
            "stop_triggered":      False,
            "updated_at":          _TS(),
        }
        if existing:
            alert_id = existing["alert_id"]
            ref.document(alert_id).update(payload)
        else:
            payload["created_at"] = _TS()
            _, doc_ref = ref.add(payload)
            alert_id = doc_ref.id
        return alert_id
    except Exception:
        return None


def update_alert(
    uid: str,
    alert_id: str,
    target_price: float,
    stop_loss: float,
    notification_enabled: bool,
) -> bool:
    ref = _stocks_ref(uid)
    if ref is None:
        return False
    try:
        ref.document(alert_id).update({
            "target_price":        float(target_price),
            "stop_loss":           float(stop_loss),
            "notification_enabled": notification_enabled,
            "target_triggered":    False,
            "stop_triggered":      False,
            "updated_at":          _TS(),
        })
        return True
    except Exception:
        return False


def delete_alert(uid: str, alert_id: str) -> bool:
    ref = _stocks_ref(uid)
    if ref is None:
        return False
    try:
        ref.document(alert_id).delete()
        return True
    except Exception:
        return False


def toggle_notification(uid: str, alert_id: str, enabled: bool) -> bool:
    ref = _stocks_ref(uid)
    if ref is None:
        return False
    try:
        ref.document(alert_id).update({
            "notification_enabled": enabled,
            "updated_at": _TS(),
        })
        return True
    except Exception:
        return False


def mark_triggered(uid: str, alert_id: str, trigger_type: str, trigger_price: float, alert_price: float) -> bool:
    """
    trigger_type: 'target' or 'stop_loss'
    trigger_price: the user's set target/stop value
    alert_price: current market price when triggered
    """
    ref = _stocks_ref(uid)
    hist = _history_ref(uid)
    if ref is None:
        return False
    try:
        field = "target_triggered" if trigger_type == "target" else "stop_triggered"
        ref.document(alert_id).update({field: True, "updated_at": _TS()})

        if hist is not None:
            doc = ref.document(alert_id).get()
            symbol = doc.to_dict().get("stock_symbol", "") if doc.exists else ""
            hist.add({
                "stock_symbol":  symbol,
                "trigger_type":  trigger_type,
                "trigger_price": trigger_price,
                "alert_price":   alert_price,
                "triggered_at":  _TS() or datetime.now(timezone.utc).isoformat(),
            })
        return True
    except Exception:
        return False
