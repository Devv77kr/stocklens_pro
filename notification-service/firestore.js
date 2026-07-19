'use strict';
// firestore.js ── Firebase Admin SDK init + alert query helpers

require('dotenv').config();
const admin = require('firebase-admin');

// ── init (idempotent) ─────────────────────────────────────────────────────────
if (!admin.apps.length) {
  admin.initializeApp({
    credential: admin.credential.cert({
      projectId:   process.env.FIREBASE_PROJECT_ID,
      privateKey:  (process.env.FIREBASE_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
      clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
    }),
  });
}

const db = admin.firestore();

function getDb() {
  return db;
}

/**
 * Fetch all active price-alert documents across all users using a
 * Firestore collection-group query on the 'stocks' sub-collection.
 *
 * Returns an array of plain objects:
 *   { uid, alertId, stock_symbol, target_price, stop_loss,
 *     target_triggered, stop_triggered, notification_enabled,
 *     userName, userEmail }
 */
async function getAllActiveAlerts() {
  // collection group query — needs index: notification_enabled ASC
  const snap = await db
    .collectionGroup('stocks')
    .where('notification_enabled', '==', true)
    .get();

  if (snap.empty) return [];

  // Collect unique UIDs so we can batch-fetch user profiles
  const alerts = [];
  const uids   = new Set();

  snap.forEach(doc => {
    const data = doc.data();
    // Skip if both already triggered
    if (data.target_triggered && data.stop_triggered) return;

    // doc.ref.path = price_alerts/{uid}/stocks/{alertId}
    const parts = doc.ref.path.split('/');
    const uid       = parts[1];
    const alertId   = parts[3];

    uids.add(uid);
    alerts.push({ ...data, uid, alertId });
  });

  if (alerts.length === 0) return [];

  // Batch-fetch user docs for email + name
  const userMap = {};
  await Promise.all(
    [...uids].map(async uid => {
      try {
        const userDoc = await db.collection('users').document
          ? db.collection('users').doc(uid).get()
          : null;
        if (userDoc && userDoc.exists) {
          const u = userDoc.data();
          userMap[uid] = {
            email: u.email || '',
            name:  u.display_name || u.name || 'Investor',
          };
        }
      } catch (_) {}
    })
  );

  return alerts.map(a => ({
    ...a,
    userEmail: userMap[a.uid]?.email || '',
    userName:  userMap[a.uid]?.name  || 'Investor',
  }));
}

/**
 * Mark an alert as triggered and log to alert_history.
 * triggerType: 'target' | 'stop_loss'
 */
async function markTriggered(uid, alertId, triggerType, triggerPrice, alertPrice, stockSymbol) {
  const field = triggerType === 'target' ? 'target_triggered' : 'stop_triggered';

  await db
    .collection('price_alerts')
    .doc(uid)
    .collection('stocks')
    .doc(alertId)
    .update({
      [field]:    true,
      updated_at: admin.firestore.FieldValue.serverTimestamp(),
    });

  // Write history log
  await db
    .collection('alert_history')
    .doc(uid)
    .collection('logs')
    .add({
      stock_symbol:  stockSymbol,
      trigger_type:  triggerType,
      trigger_price: triggerPrice,
      alert_price:   alertPrice,
      triggered_at:  admin.firestore.FieldValue.serverTimestamp(),
    });
}

module.exports = { getDb, getAllActiveAlerts, markTriggered };
