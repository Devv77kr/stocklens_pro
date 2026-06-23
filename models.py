# models.py  ── ML Forecasting: LSTM · XGBoost · GBR · RF · Ensemble

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings
warnings.filterwarnings("ignore")


# ── Feature Engineering ────────────────────────────────────────────────────────
def build_features(close: np.ndarray, lags: int = 30) -> tuple:
    """
    Creates a rich feature matrix from price series.
    All features are NORMALIZED (ratios/returns) to remove price-level bias.
    Target is next-day RETURN (not raw price).
    """
    s = pd.Series(close)
    df = pd.DataFrame()

    # Lag price RATIOS (normalized to current price — no raw price leak)
    for lag in [1, 2, 3, 5, 10, 15, 20, 25, 30]:
        if lag <= lags:
            df[f"lag_ratio_{lag}"] = s.shift(lag) / s

    # Returns (already scale-free)
    for n in [1, 3, 5, 10, 20]:
        df[f"ret_{n}"] = s.pct_change(n)

    # Rolling stats as RATIOS to current price
    for w in [5, 10, 20, 30]:
        df[f"ma_ratio_{w}"]  = s.rolling(w).mean() / s
        df[f"std_pct_{w}"]   = s.rolling(w).std() / s
        df[f"min_ratio_{w}"] = s.rolling(w).min() / s
        df[f"max_ratio_{w}"] = s.rolling(w).max() / s

    # RSI proxy (already 0-100 scale, no change needed)
    delta = s.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    # EMA crossover — normalized as percentage of price
    ema12 = s.ewm(span=12).mean()
    ema26 = s.ewm(span=26).mean()
    df["macd_pct"] = (ema12 - ema26) / s

    # TARGET: next-day RETURN (not raw price)
    df["target"] = s.pct_change().shift(-1)

    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    X = df.drop("target", axis=1).values
    y = df["target"].values
    return X, y, df.index


# ── LSTM ──────────────────────────────────────────────────────────────────────
def train_lstm(scaled: np.ndarray, look_back: int = 60, epochs: int = 30):
    try:
        import tensorflow as tf
        tf.get_logger().setLevel("ERROR")

        X, y = [], []
        for i in range(look_back, len(scaled)):
            X.append(scaled[i - look_back:i])
            y.append(scaled[i])
        X, y = np.array(X), np.array(y)

        split = int(len(X) * 0.85)
        X_tr, X_te = X[:split], X[split:]
        y_tr, y_te = y[:split], y[split:]

        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(128, return_sequences=True,
                                 input_shape=(look_back, 1),
                                 kernel_regularizer=tf.keras.regularizers.l2(1e-4)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1),
        ])
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="mse")

        cb = [tf.keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True),
              tf.keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=3, verbose=0)]
        model.fit(X_tr, y_tr, validation_split=0.1, epochs=epochs, batch_size=32,
                  callbacks=cb, verbose=0)

        y_pred_te = model.predict(X_te, verbose=0).flatten()
        return model, X_te, y_te, y_pred_te, look_back
    except ImportError:
        return None, None, None, None, None


def forecast_lstm(model, scaled: np.ndarray, scaler, n_days: int, look_back: int,
                  last_price: float = None):
    """Forecast n_days ahead. Set last_price to reconstruct prices from returns."""
    window = list(scaled[-look_back:].flatten())
    preds_scaled = []
    for _ in range(n_days):
        x_in = np.array(window[-look_back:]).reshape(1, look_back, 1)
        p    = model.predict(x_in, verbose=0)[0, 0]
        preds_scaled.append(p)
        window.append(p)
    raw = scaler.inverse_transform(np.array(preds_scaled).reshape(-1, 1)).flatten()
    if last_price is not None:
        # raw values are predicted returns → chain-multiply to get prices
        prices = []
        current = last_price
        for r in raw:
            current = current * (1 + r)
            prices.append(current)
        return np.array(prices)
    return raw


# ── Sklearn Models ────────────────────────────────────────────────────────────
def train_sklearn(close: np.ndarray, model_name: str = "xgb"):
    X, y, idx = build_features(close)
    split = int(len(X) * 0.85)
    X_tr, X_te = X[:split], X[split:]
    y_tr, y_te = y[:split], y[split:]

    if model_name == "xgb":
        try:
            from xgboost import XGBRegressor
            m = XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.03,
                             subsample=0.8, colsample_bytree=0.8,
                             min_child_weight=3, gamma=0.1,
                             reg_alpha=0.05, reg_lambda=1.0,
                             random_state=42, verbosity=0)
        except ImportError:
            m = GradientBoostingRegressor(n_estimators=300, max_depth=4,
                                          learning_rate=0.05, random_state=42)
    elif model_name == "gbr":
        m = GradientBoostingRegressor(n_estimators=300, max_depth=4,
                                      learning_rate=0.05, random_state=42)
    elif model_name == "rf":
        m = RandomForestRegressor(n_estimators=200, max_depth=8,
                                  min_samples_leaf=5, random_state=42, n_jobs=-1)
    else:  # ridge
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        m = Pipeline([("sc", StandardScaler()), ("r", Ridge(alpha=10.0))])

    m.fit(X_tr, y_tr)
    y_pred_te = m.predict(X_te)
    return m, X_te, y_te, y_pred_te


def forecast_sklearn(model, close_arr: np.ndarray, n_days: int):
    """Rolling forecast: predict next-day RETURN, convert to price, repeat."""
    prices = list(close_arr.copy())
    preds  = []
    for _ in range(n_days):
        s = pd.Series(prices)
        X_row = _single_feature_row(s)
        predicted_return = model.predict(X_row)[0]
        next_price = prices[-1] * (1 + predicted_return)
        preds.append(next_price)
        prices.append(next_price)
    return np.array(preds)


def _single_feature_row(s: pd.Series) -> np.ndarray:
    """Build the SAME normalized feature vector as build_features for one row."""
    curr = s.iloc[-1]
    df = pd.DataFrame()
    for lag in [1, 2, 3, 5, 10, 15, 20, 25, 30]:
        df[f"lag_ratio_{lag}"] = [s.iloc[-lag] / curr if len(s) > lag else np.nan]
    for n in [1, 3, 5, 10, 20]:
        df[f"ret_{n}"] = [s.pct_change(n).iloc[-1] if len(s) > n else np.nan]
    for w in [5, 10, 20, 30]:
        df[f"ma_ratio_{w}"]  = [s.rolling(w).mean().iloc[-1] / curr if len(s) >= w else np.nan]
        df[f"std_pct_{w}"]   = [s.rolling(w).std().iloc[-1] / curr  if len(s) >= w else np.nan]
        df[f"min_ratio_{w}"] = [s.rolling(w).min().iloc[-1] / curr  if len(s) >= w else np.nan]
        df[f"max_ratio_{w}"] = [s.rolling(w).max().iloc[-1] / curr  if len(s) >= w else np.nan]
    delta = s.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi"]      = [100 - (100 / (1 + gain.iloc[-1] / max(loss.iloc[-1], 1e-9)))]
    ema12          = s.ewm(span=12).mean()
    ema26          = s.ewm(span=26).mean()
    df["macd_pct"] = [(ema12.iloc[-1] - ema26.iloc[-1]) / curr]
    return df.values
    
# ── Ensemble ─────────────────────────────────────────────────────────────────
def ensemble_forecast(forecasts: dict, weights: dict = None) -> np.ndarray:
    """
    forecasts: {model_name: np.ndarray of shape (n_days,)}
    weights:   optional dict of {model_name: float}
    """
    keys = list(forecasts.keys())
    if weights is None:
        weights = {k: 1.0 for k in keys}
    total_w = sum(weights.values())
    result  = np.zeros(len(next(iter(forecasts.values()))))
    for k in keys:
        result += np.asarray(forecasts[k]) * (weights[k] / total_w)
    return result


# ── Metrics ───────────────────────────────────────────────────────────────────
def evaluate(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Evaluate return predictions. y_true/y_pred are daily returns."""
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    # SMAPE: works better than MAPE when values are near zero (common for returns)
    mape = np.mean(2 * np.abs(y_true - y_pred) /
                   (np.abs(y_true) + np.abs(y_pred) + 1e-9)) * 100
    # Directional accuracy: did we predict the correct sign (up/down)?
    da   = np.mean(np.sign(y_true) == np.sign(y_pred)) * 100
    return {"MAE": mae, "RMSE": rmse, "R²": r2, "MAPE %": mape, "Dir. Acc %": da}


# ── Risk Metrics ──────────────────────────────────────────────────────────────
def risk_metrics(close: pd.Series, rf_annual: float = 0.05) -> dict:
    returns = close.pct_change().dropna()
    rf_daily = rf_annual / 252

    # Sharpe / Sortino
    excess  = returns - rf_daily
    sharpe  = excess.mean() / excess.std() * np.sqrt(252)
    neg_ret = returns[returns < 0]
    sortino = excess.mean() / neg_ret.std() * np.sqrt(252)

    # Drawdown
    roll_max  = close.cummax()
    drawdown  = (close - roll_max) / roll_max
    max_dd    = drawdown.min()
    calmar    = (returns.mean() * 252) / abs(max_dd) if max_dd != 0 else np.nan

    # VaR / CVaR
    var_95  = np.percentile(returns, 5)
    var_99  = np.percentile(returns, 1)
    cvar_95 = returns[returns <= var_95].mean()
    cvar_99 = returns[returns <= var_99].mean()

    # Volatility
    ann_vol = returns.std() * np.sqrt(252)
    monthly_vol = returns.std() * np.sqrt(21)

    return {
        "Sharpe Ratio":      float(sharpe),
        "Sortino Ratio":     float(sortino),
        "Calmar Ratio":      float(calmar),
        "Ann. Volatility":   float(ann_vol * 100),
        "Monthly Volatility":float(monthly_vol * 100),
        "Max Drawdown":      float(max_dd * 100),
        "VaR 95%":           float(var_95 * 100),
        "VaR 99%":           float(var_99 * 100),
        "CVaR 95%":          float(cvar_95 * 100),
        "CVaR 99%":          float(cvar_99 * 100),
        "Ann. Return":       float(returns.mean() * 252 * 100),
        "Skewness":          float(returns.skew()),
        "Kurtosis":          float(returns.kurtosis()),
    }


# ── Monte Carlo ───────────────────────────────────────────────────────────────
def monte_carlo(close: pd.Series, n_days: int = 30, n_sims: int = 1000,
                seed: int = 42) -> np.ndarray:
    """Returns array (n_sims, n_days+1) of simulated price paths."""
    np.random.seed(seed)
    returns  = close.pct_change().dropna()
    mu       = returns.mean()
    sigma    = returns.std()
    last     = close.iloc[-1]
    dt       = 1
    paths    = np.zeros((n_sims, n_days + 1))
    paths[:, 0] = last
    for t in range(1, n_days + 1):
        z = np.random.standard_normal(n_sims)
        paths[:, t] = paths[:, t-1] * np.exp(
            (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
        )
    return paths


# ── Strategy Backtesting ──────────────────────────────────────────────────────
def backtest_ma_crossover(close: pd.Series, fast: int = 20, slow: int = 50) -> dict:
    ma_f   = close.rolling(fast).mean()
    ma_s   = close.rolling(slow).mean()
    signal = (ma_f > ma_s).astype(int).shift(1)    # 1=long, 0=cash

    daily_ret  = close.pct_change()
    strat_ret  = (signal * daily_ret).dropna()
    bh_ret     = daily_ret.dropna()

    strat_cum  = (1 + strat_ret).cumprod()
    bh_cum     = (1 + bh_ret).cumprod()

    trades     = signal.diff().abs().sum()

    return {
        "strat_returns": strat_ret,
        "bh_returns":    bh_ret,
        "strat_cum":     strat_cum,
        "bh_cum":        bh_cum,
        "strat_total":   strat_cum.iloc[-1] - 1,
        "bh_total":      bh_cum.iloc[-1] - 1,
        "num_trades":    int(trades / 2),
        "strat_sharpe":  strat_ret.mean() / strat_ret.std() * np.sqrt(252),
        "bh_sharpe":     bh_ret.mean() / bh_ret.std() * np.sqrt(252),
        "dates":         close.index,
    }


def backtest_rsi_strategy(close: pd.Series, oversold: int = 30, overbought: int = 70) -> dict:
    from indicators import rsi as calc_rsi
    r      = calc_rsi(close, 14)
    pos    = pd.Series(0, index=close.index)
    in_pos = False
    for i in range(1, len(r)):
        if not in_pos and r.iloc[i] < oversold:
            in_pos = True
        elif in_pos and r.iloc[i] > overbought:
            in_pos = False
        pos.iloc[i] = 1 if in_pos else 0

    daily_ret  = close.pct_change()
    strat_ret  = (pos.shift(1) * daily_ret).dropna()
    bh_ret     = daily_ret.dropna()
    strat_cum  = (1 + strat_ret).cumprod()
    bh_cum     = (1 + bh_ret).cumprod()
    trades     = pos.diff().abs().sum()

    return {
        "strat_returns": strat_ret,
        "bh_returns":    bh_ret,
        "strat_cum":     strat_cum,
        "bh_cum":        bh_cum,
        "strat_total":   strat_cum.iloc[-1] - 1,
        "bh_total":      bh_cum.iloc[-1] - 1,
        "num_trades":    int(trades / 2),
        "strat_sharpe":  strat_ret.mean() / strat_ret.std() * np.sqrt(252),
        "bh_sharpe":     bh_ret.mean() / bh_ret.std() * np.sqrt(252),
        "dates":         close.index,
    }