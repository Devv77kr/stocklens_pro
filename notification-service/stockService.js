'use strict';
// stockService.js ── Yahoo Finance price fetching via native fetch (Node 18+)

/**
 * Fetch the latest market price for a single symbol.
 * Uses Yahoo Finance v8 chart API — no third-party library needed.
 * Returns null if the symbol can't be resolved.
 */
async function fetchPrice(symbol) {
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=1d&range=1d`;
    const res  = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    if (!res.ok) {
      console.warn(`[stockService] HTTP ${res.status} for ${symbol}`);
      return null;
    }
    const data  = await res.json();
    const price = data?.chart?.result?.[0]?.meta?.regularMarketPrice;
    return price != null ? Number(price) : null;
  } catch (err) {
    console.warn(`[stockService] fetchPrice failed for ${symbol}: ${err.message}`);
    return null;
  }
}

/**
 * Fetch prices for multiple symbols concurrently.
 * Returns a Map<symbol, price|null>.
 */
async function fetchPrices(symbols) {
  const unique = [...new Set(symbols)];
  const results = await Promise.allSettled(unique.map(s => fetchPrice(s)));

  const map = new Map();
  unique.forEach((sym, i) => {
    const r = results[i];
    map.set(sym, r.status === 'fulfilled' ? r.value : null);
  });
  return map;
}

module.exports = { fetchPrice, fetchPrices };
