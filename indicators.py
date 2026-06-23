# indicators.py  ── Technical Analysis Indicators

import numpy as np
import pandas as pd


# ── Trend ──────────────────────────────────────────────────────────────────────
def sma(series: pd.Series, n: int) -> pd.Series:
    return series.rolling(n).mean()

def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()

def bollinger_bands(close: pd.Series, n: int = 20, std_mult: float = 2.0):
    mid  = sma(close, n)
    std  = close.rolling(n).std()
    return mid - std_mult * std, mid, mid + std_mult * std   # (lower, mid, upper)

def ichimoku(high, low, close):
    tenkan  = (high.rolling(9).max()  + low.rolling(9).min())  / 2
    kijun   = (high.rolling(26).max() + low.rolling(26).min()) / 2
    senkou_a = ((tenkan + kijun) / 2).shift(26)
    senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
    chikou  = close.shift(-26)
    return tenkan, kijun, senkou_a, senkou_b, chikou


# ── Momentum ───────────────────────────────────────────────────────────────────
def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0).ewm(com=n-1, adjust=False).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=n-1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(close: pd.Series, fast=12, slow=26, signal=9):
    macd_line  = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram

def stochastic(high, low, close, k=14, d=3):
    lo_k = low.rolling(k).min()
    hi_k = high.rolling(k).max()
    k_line = 100 * (close - lo_k) / (hi_k - lo_k).replace(0, np.nan)
    d_line = k_line.rolling(d).mean()
    return k_line, d_line

def williams_r(high, low, close, n=14):
    hi = high.rolling(n).max()
    lo = low.rolling(n).min()
    return -100 * (hi - close) / (hi - lo).replace(0, np.nan)

def cci(high, low, close, n=20):
    tp  = (high + low + close) / 3
    sma_tp = tp.rolling(n).mean()
    mad    = tp.rolling(n).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    return (tp - sma_tp) / (0.015 * mad.replace(0, np.nan))

def roc(close: pd.Series, n: int = 12) -> pd.Series:
    return ((close - close.shift(n)) / close.shift(n)) * 100


# ── Volatility ─────────────────────────────────────────────────────────────────
def atr(high, low, close, n: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=n-1, adjust=False).mean()

def volatility_ratio(close: pd.Series, n: int = 14) -> pd.Series:
    """Chaikin Volatility – how quickly ATR is expanding"""
    a = atr(close, close, close, n)          # rough proxy
    return ((a - a.shift(n)) / a.shift(n)) * 100


# ── Volume ─────────────────────────────────────────────────────────────────────
def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    direction = np.sign(close.diff())
    result = (direction * volume).cumsum()
    return pd.Series(result, index=close.index) if isinstance(result, np.ndarray) else result

def vwap(high, low, close, volume) -> pd.Series:
    tp  = (high + low + close) / 3
    return (tp * volume).cumsum() / volume.cumsum()

def mfi(high, low, close, volume, n=14):
    tp = (high + low + close) / 3
    mf = tp * volume
    pos_mf = mf.where(tp > tp.shift(1), 0)
    neg_mf = mf.where(tp < tp.shift(1), 0)
    ratio  = pos_mf.rolling(n).sum() / neg_mf.rolling(n).sum().replace(0, np.nan)
    return 100 - (100 / (1 + ratio))


# ── Signal generation ──────────────────────────────────────────────────────────
def generate_signals(df: pd.DataFrame) -> dict:
    """
    Returns dict of signal_name → (signal_str, css_class)
    signal_str: 'BUY' | 'SELL' | 'HOLD' | 'NEUTRAL'
    """
    signals = {}
    c = df["Close"]

    # RSI
    r = rsi(c).iloc[-1]
    if   r < 30: signals["RSI"]     = ("BUY",  "sig-buy",  f"RSI={r:.1f} (Oversold)")
    elif r > 70: signals["RSI"]     = ("SELL", "sig-sell", f"RSI={r:.1f} (Overbought)")
    else:        signals["RSI"]     = ("HOLD", "sig-hold", f"RSI={r:.1f} (Neutral)")

    # MACD crossover
    ml, sl, _ = macd(c)
    if   ml.iloc[-1] > sl.iloc[-1] and ml.iloc[-2] <= sl.iloc[-2]:
        signals["MACD"] = ("BUY",  "sig-buy",  "MACD crossed above Signal")
    elif ml.iloc[-1] < sl.iloc[-1] and ml.iloc[-2] >= sl.iloc[-2]:
        signals["MACD"] = ("SELL", "sig-sell", "MACD crossed below Signal")
    else:
        direction = "Bullish" if ml.iloc[-1] > sl.iloc[-1] else "Bearish"
        signals["MACD"] = ("HOLD", "sig-hold", f"MACD {direction} trend")

    # Bollinger Band squeeze
    lo, mid, hi = bollinger_bands(c)
    pct_b = (c.iloc[-1] - lo.iloc[-1]) / (hi.iloc[-1] - lo.iloc[-1])
    if   pct_b < 0.1: signals["BB"]   = ("BUY",  "sig-buy",  f"%B={pct_b:.2f} (Near lower band)")
    elif pct_b > 0.9: signals["BB"]   = ("SELL", "sig-sell", f"%B={pct_b:.2f} (Near upper band)")
    else:              signals["BB"]   = ("HOLD", "sig-hold", f"%B={pct_b:.2f}")

    # MA crossover
    ma20 = sma(c, 20); ma50 = sma(c, 50)
    if   ma20.iloc[-1] > ma50.iloc[-1] and ma20.iloc[-2] <= ma50.iloc[-2]:
        signals["MA Cross"] = ("BUY",  "sig-buy",  "Golden Cross (20 > 50)")
    elif ma20.iloc[-1] < ma50.iloc[-1] and ma20.iloc[-2] >= ma50.iloc[-2]:
        signals["MA Cross"] = ("SELL", "sig-sell", "Death Cross (20 < 50)")
    else:
        trend = "Uptrend" if ma20.iloc[-1] > ma50.iloc[-1] else "Downtrend"
        signals["MA Cross"] = ("HOLD", "sig-hold", f"MA {trend}")

    # Stochastic
    k, d = stochastic(df["High"], df["Low"], c)
    k_v, d_v = k.iloc[-1], d.iloc[-1]
    if   k_v < 20 and d_v < 20: signals["Stoch"] = ("BUY",  "sig-buy",  f"%K={k_v:.0f} Oversold")
    elif k_v > 80 and d_v > 80: signals["Stoch"] = ("SELL", "sig-sell", f"%K={k_v:.0f} Overbought")
    else:                        signals["Stoch"] = ("HOLD", "sig-hold", f"%K={k_v:.0f}")

    # Williams %R
    wr = williams_r(df["High"], df["Low"], c).iloc[-1]
    if   wr < -80: signals["W%R"] = ("BUY",  "sig-buy",  f"W%R={wr:.1f} Oversold")
    elif wr > -20: signals["W%R"] = ("SELL", "sig-sell", f"W%R={wr:.1f} Overbought")
    else:          signals["W%R"] = ("HOLD", "sig-hold", f"W%R={wr:.1f}")

    # Volume trend
    vol_avg  = df["Volume"].rolling(20).mean().iloc[-1]
    vol_curr = df["Volume"].iloc[-1]
    if vol_curr > vol_avg * 1.5:
        signals["Volume"] = ("BUY" if c.diff().iloc[-1] > 0 else "SELL",
                             "sig-buy" if c.diff().iloc[-1] > 0 else "sig-sell",
                             f"High vol ({vol_curr/vol_avg:.1f}x avg)")
    else:
        signals["Volume"] = ("NEUTRAL", "sig-neu", f"Normal volume")

    return signals
