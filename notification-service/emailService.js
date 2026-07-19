'use strict';
// emailService.js ── Nodemailer transporter + HTML email templates

require('dotenv').config();
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  host:   process.env.SMTP_HOST || 'smtp.gmail.com',
  port:   parseInt(process.env.SMTP_PORT || '587', 10),
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD,
  },
});

// ── retry wrapper ─────────────────────────────────────────────────────────────
async function sendWithRetry(mailOptions, maxAttempts = 3, delayMs = 2000) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await transporter.sendMail(mailOptions);
      return;
    } catch (err) {
      if (attempt === maxAttempts) throw err;
      console.warn(`[emailService] attempt ${attempt} failed, retrying in ${delayMs}ms…`);
      await new Promise(r => setTimeout(r, delayMs));
    }
  }
}

// ── shared layout wrapper ─────────────────────────────────────────────────────
function wrapLayout(bodyContent) {
  const now = new Date().toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  });
  return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#080818;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="max-width:620px;margin:0 auto;background:#080818;">

    <!-- Header -->
    <tr>
      <td style="padding:32px 32px 20px;
                 background:linear-gradient(135deg,#141b2d 0%,#0a0e17 100%);
                 border-bottom:2px solid #00ffe0;">
        <div style="font-size:1.5rem;font-weight:800;color:#e2e8f0;letter-spacing:-0.5px;">
          stock<span style="color:#00ffe0;">lens</span>
          <span style="font-size:0.55rem;color:#64748b;font-family:'Courier New',monospace;">PRO</span>
        </div>
        <div style="font-size:0.78rem;color:#64748b;margin-top:4px;font-family:'Courier New',monospace;">
          🚨 PRICE ALERT · ${now}
        </div>
      </td>
    </tr>

    ${bodyContent}

    <!-- Footer -->
    <tr>
      <td style="padding:16px 32px 32px;text-align:center;border-top:1px solid #1e2a3a;">
        <span style="color:#64748b;font-size:0.7rem;font-family:'Courier New',monospace;">
          StockLens Pro · AI-Powered Market Intelligence<br>
          ⚠️ Not financial advice. For informational purposes only.
        </span>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

// ── Target reached email ──────────────────────────────────────────────────────
async function sendTargetAlert(toEmail, userName, symbol, currentPrice, targetPrice) {
  const fname = (userName || 'Investor').split(' ')[0];
  const fmt   = n => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const sym   = symbol.endsWith('.NS') || symbol.endsWith('.BO') ? '₹' : '$';

  const body = `
    <tr>
      <td style="padding:24px 32px 12px;">
        <p style="color:#e2e8f0;font-size:1rem;margin:0 0 8px;">
          Hey <strong style="color:#00ffe0;">${fname}</strong>! 👋
        </p>
        <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.6;">
          Great news — your <strong style="color:#00ffe0;">target price</strong> has been reached!
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:0 32px 24px;">
        <div style="background:#141b2d;border:1px solid rgba(34,197,94,0.4);border-radius:12px;
                    padding:1.4rem;border-left:4px solid #22c55e;">
          <div style="font-family:'Courier New',monospace;font-size:1.3rem;font-weight:700;
                      color:#e2e8f0;margin-bottom:1rem;">⭐ ${symbol}</div>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:6px 0;color:#64748b;font-family:'Courier New',monospace;font-size:0.82rem;">Current Price</td>
              <td style="padding:6px 0;color:#22c55e;font-weight:700;font-family:'Courier New',monospace;
                         text-align:right;font-size:1rem;">${sym}${fmt(currentPrice)}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#64748b;font-family:'Courier New',monospace;font-size:0.82rem;">Your Target</td>
              <td style="padding:6px 0;color:#22c55e;font-family:'Courier New',monospace;
                         text-align:right;font-size:0.9rem;">${sym}${fmt(targetPrice)}</td>
            </tr>
          </table>
          <div style="margin-top:1rem;background:rgba(34,197,94,0.12);color:#22c55e;
                      border:1px solid rgba(34,197,94,0.3);border-radius:8px;padding:10px 16px;
                      font-family:'Courier New',monospace;font-size:0.82rem;font-weight:700;">
            ↑ TARGET REACHED — Consider reviewing your position
          </div>
        </div>
      </td>
    </tr>`;

  await sendWithRetry({
    from:    process.env.EMAIL_FROM,
    to:      toEmail,
    subject: `🎯 StockLens Pro — Target Reached: ${symbol} @ ${sym}${fmt(currentPrice)}`,
    html:    wrapLayout(body),
    text:    `StockLens Pro Alert\n\n${fname}, your target for ${symbol} has been reached!\nCurrent: ${sym}${fmt(currentPrice)}\nTarget: ${sym}${fmt(targetPrice)}\n\nNot financial advice.`,
  });
}

// ── Stop-loss triggered email ─────────────────────────────────────────────────
async function sendStopLossAlert(toEmail, userName, symbol, currentPrice, stopLoss) {
  const fname = (userName || 'Investor').split(' ')[0];
  const fmt   = n => n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const sym   = symbol.endsWith('.NS') || symbol.endsWith('.BO') ? '₹' : '$';

  const body = `
    <tr>
      <td style="padding:24px 32px 12px;">
        <p style="color:#e2e8f0;font-size:1rem;margin:0 0 8px;">
          Hey <strong style="color:#00ffe0;">${fname}</strong>! 👋
        </p>
        <p style="color:#64748b;font-size:0.88rem;margin:0;line-height:1.6;">
          Your <strong style="color:#ff4d6d;">stop-loss price</strong> has been triggered.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:0 32px 24px;">
        <div style="background:#141b2d;border:1px solid rgba(255,77,109,0.4);border-radius:12px;
                    padding:1.4rem;border-left:4px solid #ff4d6d;">
          <div style="font-family:'Courier New',monospace;font-size:1.3rem;font-weight:700;
                      color:#e2e8f0;margin-bottom:1rem;">⭐ ${symbol}</div>
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td style="padding:6px 0;color:#64748b;font-family:'Courier New',monospace;font-size:0.82rem;">Current Price</td>
              <td style="padding:6px 0;color:#ff4d6d;font-weight:700;font-family:'Courier New',monospace;
                         text-align:right;font-size:1rem;">${sym}${fmt(currentPrice)}</td>
            </tr>
            <tr>
              <td style="padding:6px 0;color:#64748b;font-family:'Courier New',monospace;font-size:0.82rem;">Your Stop Loss</td>
              <td style="padding:6px 0;color:#ff4d6d;font-family:'Courier New',monospace;
                         text-align:right;font-size:0.9rem;">${sym}${fmt(stopLoss)}</td>
            </tr>
          </table>
          <div style="margin-top:1rem;background:rgba(255,77,109,0.12);color:#ff4d6d;
                      border:1px solid rgba(255,77,109,0.3);border-radius:8px;padding:10px 16px;
                      font-family:'Courier New',monospace;font-size:0.82rem;font-weight:700;">
            ↓ STOP LOSS HIT — The stock has fallen below your floor
          </div>
        </div>
      </td>
    </tr>`;

  await sendWithRetry({
    from:    process.env.EMAIL_FROM,
    to:      toEmail,
    subject: `🔴 StockLens Pro — Stop Loss Triggered: ${symbol} @ ${sym}${fmt(currentPrice)}`,
    html:    wrapLayout(body),
    text:    `StockLens Pro Alert\n\n${fname}, stop-loss triggered for ${symbol}!\nCurrent: ${sym}${fmt(currentPrice)}\nStop Loss: ${sym}${fmt(stopLoss)}\n\nNot financial advice.`,
  });
}

module.exports = { sendTargetAlert, sendStopLossAlert };
