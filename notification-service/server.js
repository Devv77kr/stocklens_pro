'use strict';
// server.js ── StockLens Pro Notification Service entry point

require('dotenv').config();

const express              = require('express');
const { startScheduler, checkAlerts, getLastCheckTime } = require('./scheduler');

const app  = express();
const PORT = process.env.PORT || 3001;

app.use(express.json());

// ── Health check ──────────────────────────────────────────────────────────────
app.get('/health', (_req, res) => {
  res.json({
    status:    'ok',
    service:   'stocklens-notification-service',
    uptime:    process.uptime(),
    lastCheck: getLastCheckTime()?.toISOString() || null,
    timestamp: new Date().toISOString(),
  });
});

// ── Manual trigger (useful for testing without waiting for cron) ──────────────
app.post('/check', async (_req, res) => {
  try {
    await checkAlerts();
    res.json({ status: 'ok', message: 'Alert check completed', timestamp: new Date().toISOString() });
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message });
  }
});

// ── Start server + scheduler ──────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[server] StockLens Pro Notification Service running on port ${PORT}`);
  const interval = parseInt(process.env.CHECK_INTERVAL_SECONDS || '60', 10);
  startScheduler(interval);
});

module.exports = app;
