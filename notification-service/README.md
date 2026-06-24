# StockLens Pro — Notification Service

Autonomous Node.js service that monitors Firestore price alerts every 60 seconds and sends emails via Nodemailer when target or stop-loss conditions are met.

## Setup

```bash
cd notification-service
npm install
cp .env.example .env   # fill in your credentials
node server.js
```

## .env values

| Key | Description |
|-----|-------------|
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | Gmail App Password (16 chars, not your account password) |
| `FIREBASE_PROJECT_ID` | From Firebase Console → Project Settings |
| `FIREBASE_PRIVATE_KEY` | From service account JSON (keep the `\n` line breaks) |
| `FIREBASE_CLIENT_EMAIL` | From service account JSON |
| `CHECK_INTERVAL_SECONDS` | How often to poll (default: 60) |

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service status + last check time |
| POST | `/check` | Trigger an immediate price check |

## How it works

1. Every `CHECK_INTERVAL_SECONDS`, the scheduler queries `price_alerts/*/stocks` (collection group) for all docs where `notification_enabled == true`.
2. Fetches live prices via `yahoo-finance2`.
3. Compares each alert's `target_price` and `stop_loss` to the current price.
4. Sends a styled HTML email via Nodemailer if a condition is met.
5. Updates `target_triggered` or `stop_triggered` in Firestore to prevent duplicate emails.
6. Writes a log entry to `alert_history/{uid}/logs`.

## Firestore index required

For the collection group query to work, create a composite index in Firebase Console:

- Collection group: `stocks`
- Field: `notification_enabled` — Ascending
- Query scope: Collection group

Firebase will prompt you with a direct link when you first run the service.

## Gmail App Password

1. Go to myaccount.google.com → Security → 2-Step Verification → App passwords
2. Generate a password for "Mail" / "Other (StockLens Pro)"
3. Paste the 16-character password into `SMTP_PASSWORD`
