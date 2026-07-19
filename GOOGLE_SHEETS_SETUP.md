# 📊 StockLens Pro - Google Sheets Integration Setup Guide

## ✅ Step 1: Create a Google Sheet

1. Go to **Google Sheets** → https://sheets.google.com/
2. Click **"+ Create"** → Choose **Blank spreadsheet**
3. Name it: **"StockLens Pro - Expert Recommendations"**

---

## ✅ Step 2: Create Sheet Tabs

Create these worksheet tabs at the bottom:
- **Experts Recommendations** (Main data sheet)
- **Expert Directory** (Optional - Expert info)
- **Stock Symbols** (Optional - Reference data)

---

## ✅ Step 3: Set Up "Experts Recommendations" Sheet

### Column Headers (Row 1):
Copy and paste these exact headers:

| Column | Header | Type | Example |
|--------|--------|------|---------|
| A | Company | Text | Tata Consultancy Services |
| B | Ticker | Text | TCS |
| C | Signal | Text | BUY or SELL |
| D | Term | Text | Short Term, Medium Term, Long Term |
| E | Entry Price | Number | 2080.00 |
| F | Target Price | Number | 2300.00 |
| G | Expert | Text | Analyst Name or ID |
| H | Rating | Number (1-5) | 5 |
| I | Confidence % | Number (0-100) | 82.5 |
| J | Accuracy % | Number (0-100) | 78.5 |

### Row 1 (Headers):
```
Company | Ticker | Signal | Term | Entry Price | Target Price | Expert | Rating | Confidence % | Accuracy %
```

---

## ✅ Step 4: Add Sample Data

### Example Data (Rows 2 onwards):

```
Tata Consultancy Services | TCS | BUY | Short Term | 2080.00 | 2300.00 | Expert Analyst 1 | 5 | 82.5 | 78.5
Tata Consultancy Services | TCS | BUY | Medium Term | 2050.00 | 2400.00 | Expert Analyst 2 | 4 | 75.0 | 72.0
Reliance Industries | RELIANCE.NS | BUY | Long Term | 2900.00 | 3500.00 | Senior Analyst | 5 | 88.0 | 85.0
Infosys Limited | INFY | SELL | Short Term | 1850.00 | 1650.00 | Technical Expert | 3 | 65.0 | 62.0
HDFC Bank | HDFCBANK.NS | BUY | Medium Term | 1600.00 | 1900.00 | Fundamental Analyst | 5 | 90.0 | 87.5
```

---

## ✅ Step 5: Format the Sheet

### Column Widths:
1. Select **Column A** → Set width to **200px**
2. Select **Column B** → Set width to **80px**
3. Select **Column C** → Set width to **80px**
4. Select **Column D** → Set width to **120px**
5. Select **Columns E-F** → Set width to **120px**
6. Select **Columns G-J** → Set width to **100px**

### Format Numbers:
1. Select **Columns E & F** (Prices)
2. Format → Number → Custom number format → **0.00**

3. Select **Columns I & J** (Percentages)
4. Format → Number → Percent → **0.0%**

### Format Headers (Row 1):
1. Select entire **Row 1**
2. Format → Fill color → Light gray/blue (your choice)
3. Format → Text → Bold and center align

### Data Validation:
For **Column C (Signal)**:
1. Select cells C2:C1000
2. Data → Validation
3. Choose **List of items** → Type: `BUY,SELL`

For **Column D (Term)**:
1. Select cells D2:D1000
2. Data → Validation
3. Choose **List of items** → Type: `Short Term,Medium Term,Long Term`

---

## ✅ Step 6: Share the Sheet

### Make it Accessible:
1. Click **Share** (top-right)
2. Click **"Change to anyone with the link"**
3. Set permission to **"Viewer"** or **"Editor"**
4. Copy the sharing link

### Get the Sheet URL:
The URL format should be:
```
https://docs.google.com/spreadsheets/d/SHEET_ID/edit
```

**Copy this entire URL** - you'll need it in the next step.

---

## ✅ Step 7: Connect to StockLens Pro App

### Update `app.py`:

Find this line (around line 860):
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

**Replace it with your actual Google Sheet URL:**
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/YOUR_ACTUAL_SHEET_ID/edit"
```

### Example:
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p/edit"
```

---

## ✅ Step 8: Install Required Package

Run in terminal:
```bash
pip install gspread
```

If already installed (check requirements.txt - should be there):
```bash
pip install -r requirements.txt
```

---

## ✅ Step 9: Test the Integration

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Navigate to Tab 3** (SEBI Registered Experts' Recommendation)

3. **Check for:**
   - ✅ Expert recommendation cards loading
   - ✅ Entry/Target prices displaying correctly
   - ✅ Profit left % calculating correctly
   - ✅ Star ratings showing (⭐)
   - ✅ Confidence % displaying
   - ✅ Accuracy % displaying
   - ✅ Color-coded signals (🟢 BUY, 🔴 SELL)

---

## 🔧 Troubleshooting

### Issue: "Could not fetch from Google Sheets"

**Solution:**
1. Check if Firebase service account file exists:
   - `stocklenspro-firebase-adminsdk-fbsvc-7cf877918e.json` ✅

2. Verify sheet name is exactly **"Experts Recommendations"**
   - Go to Google Sheet → Check tab name at bottom

3. Verify column headers are EXACT (case-sensitive):
   - `Company`, `Ticker`, `Signal`, `Term`, `Entry Price`, `Target Price`, `Expert`, `Rating`, `Confidence %`, `Accuracy %`

4. Test the URL manually:
   - Paste URL in browser to verify access

### Issue: Data not updating in app

**Solution:**
- App caches data for 10 minutes (ttl=600)
- Clear cache: `st.cache_data.clear()`
- Or restart Streamlit app

### Issue: "Permission denied" error

**Solution:**
1. Go to Google Sheet → **Share**
2. Change from **"Restricted"** to **"Anyone with the link"**
3. Set to **"Viewer"** access level

---

## 📋 Complete Example Google Sheet

Here's a complete example with multiple recommendations:

| Company | Ticker | Signal | Term | Entry Price | Target Price | Expert | Rating | Confidence % | Accuracy % |
|---------|--------|--------|------|-------------|--------------|--------|--------|-------------|-----------|
| Tata Consultancy Services | TCS | BUY | Short Term | 2080.00 | 2300.00 | Expert Analyst 1 | 5 | 82.5 | 78.5 |
| Tata Consultancy Services | TCS | BUY | Medium Term | 2050.00 | 2400.00 | Expert Analyst 2 | 4 | 75.0 | 72.0 |
| Reliance Industries | RELIANCE.NS | BUY | Long Term | 2900.00 | 3500.00 | Senior Analyst | 5 | 88.0 | 85.0 |
| Infosys Limited | INFY | SELL | Short Term | 1850.00 | 1650.00 | Technical Expert | 3 | 65.0 | 62.0 |
| HDFC Bank | HDFCBANK.NS | BUY | Medium Term | 1600.00 | 1900.00 | Fundamental Analyst | 5 | 90.0 | 87.5 |
| Wipro Limited | WIPRO | BUY | Short Term | 420.00 | 480.00 | Growth Analyst | 4 | 78.0 | 75.5 |
| ICICI Bank | ICICIBANK.NS | SELL | Medium Term | 780.00 | 680.00 | Value Analyst | 3 | 70.0 | 68.0 |

---

## 🎯 Features Added

✅ **Expert Ratings** - 5-star rating system (⭐)
✅ **Confidence Score** - 0-100% based on analyst confidence
✅ **Historical Accuracy** - Track expert accuracy over time
✅ **Multiple Timeframes** - Short/Medium/Long term recommendations
✅ **Real-time Profit Calculation** - "Profit Left %" from current price to target
✅ **Color-Coded Signals** - 🟢 BUY (green), 🔴 SELL (red)
✅ **Progress Bars** - Visual journey from entry to target price

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all column headers are exact
3. Ensure sheet tab is named "Experts Recommendations"
4. Check Firebase credentials file exists
5. Clear Streamlit cache and restart

---

## 🚀 Next Steps

1. ✅ Create Google Sheet with template above
2. ✅ Add your expert recommendations
3. ✅ Share the sheet and copy URL
4. ✅ Update URL in `app.py` (line 860)
5. ✅ Run app and see real recommendations!

Good luck! 📈💰
