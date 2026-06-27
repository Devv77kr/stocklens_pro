# 📡 StockLens Pro — Advanced Market Intelligence Dashboard

> **Teacher-impression level**: Production-grade fintech dashboard with 8 feature modules,
> 5 ML models, 12+ technical indicators, Monte Carlo simulation, and backtesting engine.

---
<img width="1907" height="860" alt="Screenshot 2026-06-27 234427" src="https://github.com/user-attachments/assets/52ca8c2f-2557-4758-9134-b7fb7ad41380" /

## 🏗️ Project Structure

```
stocklens_pro/
├── app.py           ← Main Streamlit dashboard (8 tabs)
├── theme.py         ← Design tokens, CSS, Plotly base layout
├── indicators.py    ← 12+ technical indicators + signal engine
├── models.py        ← ML forecasting, risk metrics, Monte Carlo, backtesting
└── requirements.txt ← All Python dependencies
```

---

## ✨ Feature Modules (8 Tabs)

### 📈 Tab 1 · Price & Volume
- Candlestick / Line charts with **MA-20, MA-50, MA-200** overlays
- **Bollinger Bands** shaded region
- **Volume bars** (green/red by direction) + 20-day volume MA
- **On-Balance Volume (OBV)** as 3rd sub-chart
- Period statistics: High, Low, Return, Volatility, Max Drawdown, Avg Daily Return
- **Up/Down day distribution** donut + daily return histogram
 

### 📡 Tab 2 · Technical Analysis
| Indicator | Description |
|---|---|
| RSI (14) | Relative Strength Index with overbought/oversold zones |
| MACD (12,26,9) | Histogram, Signal, MACD line |
| Stochastic (14,3) | %K and %D with zones |
| Williams %R | Momentum oscillator |
| CCI | Commodity Channel Index |
| ATR (14) | Average True Range (volatility) |
| MFI (14) | Money Flow Index |
| OBV | On-Balance Volume |
| Ichimoku Cloud | Full Ichimoku system (Tenkan, Kijun, Senkou A/B) |

**+ Automatic Signal Engine** generating BUY/SELL/HOLD for 7 indicators with overall score

### 🤖 Tab 3 · ML Forecast (30-Day)
| Model | Technology |
|---|---|
| **LSTM** | TensorFlow Keras (2×LSTM, Dropout, Dense) |
| **XGBoost** | Gradient boosted trees (400 estimators) |
| **Gradient Boosting** | Scikit-learn GBR |
| **Random Forest** | 200 trees, depth-8 |
| **⭐ Ensemble** | Weighted by directional accuracy |

<img width="1890" height="835" alt="Screenshot 2026-06-27 234554" src="https://github.com/user-attachments/assets/81f47f58-23e5-4e7a-aedf-4a0a71b10799" />

- Feature engineering: 30 lag prices, 5 return windows, 4 rolling stats, RSI proxy, MACD proxy
- **Confidence band** (90% CI using Brownian motion scaling)
- **Model accuracy table**: MAE, RMSE, R², MAPE, Directional Accuracy
- Day-by-day forecast table with CSV download

### ⚠️ Tab 4 · Risk Analysis
- **Sharpe, Sortino, Calmar** ratios
- **VaR 95/99%** and **CVaR 95/99%** (Expected Shortfall)
- **Max Drawdown** timeline chart
- **Rolling 252-day Sharpe** + Rolling 30-day Volatility
- **Monte Carlo Simulation** (GBM, up to 2000 paths)
  - Percentile bands: P5, P25, P50, P75, P95
  - Probability of gain/loss
- VaR bar chart comparison
- <img width="1867" height="790" alt="Screenshot 2026-06-27 235845" src="https://github.com/user-attachments/assets/54e39f0c-c8d8-4165-9fb4-9699b7f6132f" />


### 🔀 Tab 5 · Multi-Stock Comparison
- Normalised return chart (Base = 100)
- **Correlation heatmap**
- **Risk vs Return scatter plot**
- Comparative summary table (Return, Vol, Sharpe, Max DD)

### 📋 Tab 6 · Fundamentals
- 14 key financial ratios (P/E, PEG, P/B, EV/EBITDA, margins, ROE, ROA, debt ratios)
- **Financial health radar** (Profitability, Liquidity, Valuation, Growth, Efficiency)
- **Income Statement** bar chart (Revenue, Gross Profit, Operating Income, Net Income)
- **Balance Sheet** bar chart (Assets, Liabilities, Equity, Cash)

### 🎯 Tab 7 · Strategy Backtesting
- **MA Crossover strategy** (configurable fast/slow MA)
  - Cumulative return vs Buy-&-Hold, Alpha, Sharpe, # Trades
- **RSI Mean-Reversion strategy** (configurable OB/OS levels)
  - Same comparison metrics
- **Monthly Return Heatmap** (year × month calendar view)

### 📰 Tab 8 · News & Sentiment
- Per-headline **TextBlob** polarity analysis
- **Bullish/Bearish/Neutral** badges per article
- **Sentiment gauge** (-1 to +1)
- **Polarity vs Subjectivity scatter** (editorial vs fact-based)
- Bullish/Bearish/Neutral article count summary

---

## 🚀 Quick Start

```bash
# 1. Clone / navigate to project folder
cd stocklens_pro

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download TextBlob corpora (first time only)
python -m textblob.download_corpora

# 5. Launch
streamlit run app.py
```

App opens at **http://localhost:8501**

---

## 🎨 Design System

| Token | Value | Use |
|---|---|---|
| Background | `#080818` | App background |
| Teal | `#00ffe0` | Primary accent, bullish |
| Purple | `#a855f7` | Secondary accent, ML |
| Orange | `#f97316` | Warnings, MA lines |
| Red | `#ff4d6d` | Bearish, risk |
| Green | `#4ade80` | Positive signals |
| Font (mono) | IBM Plex Mono | Data, numbers |
| Font (display)| Syne | Headers, labels |

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web dashboard framework |
| `yfinance` | Real-time & historical stock data |
| `plotly` | Interactive charts |
| `scikit-learn` | GBR, RF, Ridge regression |
| `xgboost` | XGBoost regressor |
| `tensorflow` | LSTM deep learning |
| `textblob` | NLP sentiment analysis |
| `pandas / numpy` | Data processing |
| `scipy` | Statistical functions |

---

## 🔮 Extension Ideas

1. **Portfolio Optimiser**: Markowitz efficient frontier across comparison stocks
2. **Options Chain**: Implied volatility surface from yfinance
3. **ARIMA / Prophet**: Add statsmodels / Prophet for statistical forecasting
4. **Alerts System**: Email/Telegram alerts when signals fire
5. **Paper Trading**: Simulate live trades using streaming WebSocket data
6. **Sector Rotation**: Compare ETF sector performance automatically

---

*StockLens Pro — Built to impress. Built to analyse.*
