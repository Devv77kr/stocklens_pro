# alerts.py  ── StockLens Pro · Smart Prediction Gmail Alerts

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# ── HTML Email Builder ────────────────────────────────────────────────────────
def _build_html_email(user_name: str, rows: list[dict]) -> str:
    """
    rows: list of dicts with keys:
      ticker, direction, curr, pred, pct, sym
    """
    now   = datetime.now().strftime("%d %b %Y, %H:%M")
    fname = user_name.split()[0] if user_name else "Investor"

    def row_html(r: dict) -> str:
        up    = r["direction"] == "UP"
        arrow = "↑" if up else "↓"
        color = "#22c55e" if up else "#ff4d6d"
        bg    = "rgba(34,197,94,0.08)" if up else "rgba(255,77,109,0.08)"
        label = "PREDICTED UP" if up else "PREDICTED DROP"
        pct   = abs(r["pct"])
        sym   = r["sym"]
        return f"""
        <tr>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2a3a;">
            <span style="font-family:'Courier New',monospace;font-weight:700;
                         color:#e2e8f0;font-size:1rem;">{r['ticker']}</span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2a3a;text-align:center;">
            <span style="background:{bg};color:{color};border:1px solid {color};
                         border-radius:6px;padding:4px 10px;font-size:0.8rem;
                         font-weight:700;font-family:'Courier New',monospace;">
              {arrow} {label}
            </span>
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2a3a;
                     font-family:'Courier New',monospace;color:#64748b;">
            {sym}{r['curr']:,.2f}
          </td>
          <td style="padding:12px 16px;border-bottom:1px solid #1e2a3a;
                     font-family:'Courier New',monospace;color:{color};font-weight:700;">
            {sym}{r['pred']:,.2f}
            <span style="font-size:0.75rem;">({arrow}{pct:.2f}%)</span>
          </td>
        </tr>"""

    rows_html = "".join(row_html(r) for r in rows)

    up_count   = sum(1 for r in rows if r["direction"] == "UP")
    down_count = sum(1 for r in rows if r["direction"] == "DOWN")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0a0e17;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="max-width:620px;margin:0 auto;background:#0a0e17;">

    <!-- Header -->
    <tr>
      <td style="padding:32px 32px 20px;
                 background:linear-gradient(135deg,#141b2d 0%,#0a0e17 100%);
                 border-bottom:2px solid #00ffe0;">
        <div style="font-size:1.5rem;font-weight:800;color:#e2e8f0;letter-spacing:-0.5px;">
          stock<span style="color:#00ffe0;">lens</span>
          <span style="font-size:0.55rem;color:#64748b;font-family:'Courier New',monospace;">
            PRO
          </span>
        </div>
        <div style="font-size:0.78rem;color:#64748b;margin-top:4px;
                    font-family:'Courier New',monospace;">
          📡 WATCHLIST PREDICTION ALERT · {now}
        </div>
      </td>
    </tr>

    <!-- Greeting -->
    <tr>
      <td style="padding:24px 32px 12px;">
        <p style="color:#e2e8f0;font-size:1rem;margin:0 0 8px;">
          Hey <strong style="color:#00ffe0;">{fname}</strong>! 👋
        </p>
        <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.6;">
          Here's tomorrow's ML-powered prediction for your watchlist stocks.
          StockLens Pro has analysed the trend signals and here's what to watch:
        </p>
      </td>
    </tr>

    <!-- Summary badges -->
    <tr>
      <td style="padding:8px 32px 16px;">
        <span style="background:rgba(34,197,94,0.12);color:#22c55e;
                     border:1px solid rgba(34,197,94,0.3);border-radius:20px;
                     padding:5px 14px;font-size:0.78rem;font-weight:700;
                     font-family:'Courier New',monospace;margin-right:8px;">
          ↑ {up_count} PREDICTED UP
        </span>
        <span style="background:rgba(255,77,109,0.12);color:#ff4d6d;
                     border:1px solid rgba(255,77,109,0.3);border-radius:20px;
                     padding:5px 14px;font-size:0.78rem;font-weight:700;
                     font-family:'Courier New',monospace;">
          ↓ {down_count} PREDICTED DROP
        </span>
      </td>
    </tr>

    <!-- Table -->
    <tr>
      <td style="padding:0 32px 24px;">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border:1px solid #1e2a3a;border-radius:10px;overflow:hidden;">
          <thead>
            <tr style="background:#141b2d;">
              <th style="padding:10px 16px;text-align:left;color:#64748b;
                         font-size:0.72rem;font-family:'Courier New',monospace;
                         font-weight:600;letter-spacing:1px;">TICKER</th>
              <th style="padding:10px 16px;text-align:center;color:#64748b;
                         font-size:0.72rem;font-family:'Courier New',monospace;
                         font-weight:600;letter-spacing:1px;">SIGNAL</th>
              <th style="padding:10px 16px;text-align:left;color:#64748b;
                         font-size:0.72rem;font-family:'Courier New',monospace;
                         font-weight:600;letter-spacing:1px;">CURRENT</th>
              <th style="padding:10px 16px;text-align:left;color:#64748b;
                         font-size:0.72rem;font-family:'Courier New',monospace;
                         font-weight:600;letter-spacing:1px;">PREDICTED</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
      </td>
    </tr>

    <!-- Disclaimer -->
    <tr>
      <td style="padding:0 32px 16px;">
        <p style="color:#64748b;font-size:0.72rem;line-height:1.6;margin:0;
                  font-family:'Courier New',monospace;
                  border-top:1px solid #1e2a3a;padding-top:16px;">
          ⚠️ These predictions are generated by ML models for informational purposes only.
          Not financial advice. Past performance does not guarantee future results.
        </p>
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="padding:16px 32px 32px;text-align:center;
                 border-top:1px solid #1e2a3a;">
        <span style="color:#64748b;font-size:0.7rem;font-family:'Courier New',monospace;">
          StockLens Pro · AI-Powered Market Intelligence
        </span>
      </td>
    </tr>

  </table>
</body>
</html>"""


def _build_plain_text(user_name: str, rows: list[dict]) -> str:
    fname = user_name.split()[0] if user_name else "Investor"
    now   = datetime.now().strftime("%d %b %Y, %H:%M")
    lines = [
        f"StockLens Pro — Watchlist Prediction Alert",
        f"Generated: {now}",
        f"",
        f"Hey {fname}! Here's tomorrow's prediction for your watchlist:",
        f"",
    ]
    for r in rows:
        arrow = "↑ UP  " if r["direction"] == "UP" else "↓ DROP"
        lines.append(
            f"  {r['ticker']:<12} {arrow}  "
            f"{r['sym']}{r['curr']:>10,.2f}  →  "
            f"{r['sym']}{r['pred']:>10,.2f}  "
            f"({'+' if r['pct'] >= 0 else ''}{r['pct']:.2f}%)"
        )
    lines += [
        "",
        "⚠️ For informational purposes only. Not financial advice.",
        "StockLens Pro",
    ]
    return "\n".join(lines)


# ── Main Send Function ────────────────────────────────────────────────────────
def send_watchlist_alert(
    sender_email: str,
    app_password: str,
    receiver_email: str,
    user_name: str,
    card_data: list[dict],
) -> tuple[bool, str]:
    """
    Send a single combined prediction alert email for all watchlist stocks.

    card_data: list of dicts with keys:
      ticker, direction, curr, pred, pct, sym

    Returns (success: bool, message: str)
    """
    if not sender_email or not app_password or not receiver_email:
        return False, "Missing email credentials."
    if not card_data:
        return False, "Watchlist is empty — nothing to alert."

    # Filter out stocks with unknown direction
    rows = [r for r in card_data if r.get("direction") in ("UP", "DOWN")]
    if not rows:
        return False, "Could not fetch predictions for any watchlist stock."

    try:
        msg = MIMEMultipart("alternative")
        msg["From"]    = sender_email
        msg["To"]      = receiver_email
        msg["Subject"] = (
            f"📡 StockLens Pro — Watchlist Alert: "
            f"{sum(1 for r in rows if r['direction']=='UP')} ↑  "
            f"{sum(1 for r in rows if r['direction']=='DOWN')} ↓"
        )

        plain = _build_plain_text(user_name, rows)
        html  = _build_html_email(user_name, rows)

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())

        up   = sum(1 for r in rows if r["direction"] == "UP")
        down = sum(1 for r in rows if r["direction"] == "DOWN")
        return True, f"✅ Alert sent! {up} stocks ↑ UP · {down} stocks ↓ DROP"

    except smtplib.SMTPAuthenticationError:
        return False, "❌ Gmail auth failed. Check your App Password."
    except Exception as e:
        return False, f"❌ Failed to send: {e}"
