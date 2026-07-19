'use strict';
// scheduler.js ── Price-check loop: fetch prices, compare, send emails

const cron                              = require('node-cron');
const { getAllActiveAlerts, markTriggered } = require('./firestore');
const { fetchPrices }                   = require('./stockService');
const { sendTargetAlert, sendStopLossAlert } = require('./emailService');

let lastCheckTime = null;
let isRunning     = false;

async function checkAlerts() {
  if (isRunning) {
    console.log('[scheduler] Previous check still running — skipping this tick');
    return;
  }
  isRunning = true;
  lastCheckTime = new Date();

  try {
    const alerts = await getAllActiveAlerts();
    if (alerts.length === 0) {
      console.log(`[scheduler] ${lastCheckTime.toISOString()} — no active alerts`);
      return;
    }

    // Fetch prices for all unique symbols in one batch
    const symbols  = [...new Set(alerts.map(a => a.stock_symbol))];
    const priceMap = await fetchPrices(symbols);

    let emailsSent = 0;
    let errors     = 0;

    for (const alert of alerts) {
      const {
        uid, alertId, stock_symbol, company_name,
        target_price, stop_loss,
        target_triggered, stop_triggered,
        userEmail, userName,
      } = alert;

      const currentPrice = priceMap.get(stock_symbol);
      if (currentPrice == null) {
        console.warn(`[scheduler] No price for ${stock_symbol} — skipping`);
        continue;
      }

      // ── Target check ────────────────────────────────────────────────────
      if (!target_triggered && currentPrice >= target_price) {
        try {
          if (userEmail) {
            await sendTargetAlert(userEmail, userName, stock_symbol, currentPrice, target_price);
            console.log(`[scheduler] ✅ TARGET email → ${userEmail} for ${stock_symbol} @ ${currentPrice}`);
          }
          await markTriggered(uid, alertId, 'target', target_price, currentPrice, stock_symbol);
          emailsSent++;
        } catch (err) {
          console.error(`[scheduler] ❌ target email failed for ${stock_symbol}: ${err.message}`);
          errors++;
        }
      }

      // ── Stop-loss check ──────────────────────────────────────────────────
      if (!stop_triggered && currentPrice <= stop_loss) {
        try {
          if (userEmail) {
            await sendStopLossAlert(userEmail, userName, stock_symbol, currentPrice, stop_loss);
            console.log(`[scheduler] 🔴 STOP LOSS email → ${userEmail} for ${stock_symbol} @ ${currentPrice}`);
          }
          await markTriggered(uid, alertId, 'stop_loss', stop_loss, currentPrice, stock_symbol);
          emailsSent++;
        } catch (err) {
          console.error(`[scheduler] ❌ stop-loss email failed for ${stock_symbol}: ${err.message}`);
          errors++;
        }
      }
    }

    console.log(
      `[scheduler] ${lastCheckTime.toISOString()} — checked ${alerts.length} alerts | ` +
      `emails sent: ${emailsSent} | errors: ${errors}`
    );
  } catch (err) {
    console.error(`[scheduler] Fatal error in checkAlerts: ${err.message}`);
  } finally {
    isRunning = false;
  }
}

function startScheduler(intervalSeconds = 60) {
  // node-cron minimum is 1 second; clamp to 10 s floor for safety
  const interval = Math.max(10, parseInt(intervalSeconds, 10));

  // Build a cron expression: run every N seconds
  // For intervals < 60 s use seconds field; for >= 60 s use minutes
  let cronExpr;
  if (interval < 60) {
    cronExpr = `*/${interval} * * * * *`;
  } else {
    const mins = Math.floor(interval / 60);
    cronExpr = `0 */${mins} * * * *`;
  }

  console.log(`[scheduler] Starting — cron: "${cronExpr}" (~${interval}s interval)`);
  cron.schedule(cronExpr, checkAlerts, { scheduled: true });

  // Run immediately on startup
  checkAlerts();
}

function getLastCheckTime() {
  return lastCheckTime;
}

module.exports = { startScheduler, checkAlerts, getLastCheckTime };
