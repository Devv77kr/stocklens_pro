# 🧪 StockLens Pro - Integration Testing Guide

## ✅ Test 1: Verify App Starts Without Errors

### Run the App:
```bash
cd c:\Users\santo\stocklens_pro
streamlit run app.py
```

### Expected Result:
- ✅ App loads without errors
- ✅ Dashboard appears
- ✅ No red error messages in terminal

### Troubleshooting:
If you see errors:
```bash
# Check Python version
python --version

# Install missing packages
pip install -r requirements.txt

# Clear Streamlit cache
streamlit cache clear

# Run again
streamlit run app.py
```

---

## ✅ Test 2: Navigate to Tab 3 (SEBI Experts)

### Steps:
1. Open the app → http://localhost:8501
2. Look for 8 tabs at the top
3. Click on **Tab 3** or scroll to find "SEBI Registered Experts' Recommendation"

### Expected Result:
- ✅ Tab loads without errors
- ✅ You see expert recommendation cards
- ✅ Each card shows:
  - 🟢 BUY or 🔴 SELL signal
  - Company name
  - Entry & Target prices
  - Profit left %
  - Star ratings (⭐)
  - Confidence %
  - Accuracy %

---

## ✅ Test 3: Verify Demo Data Works

### What You Should See (Without Google Sheets):

```
📊 Expert Analyst 1
Tata Consultancy Services (TCS)
🟢 BUY · Short Term

Entry Price: ₹[price]
Target Price: ₹[higher price]
Profit Left: 💰 +10.50%

⭐⭐⭐⭐⭐ (5 stars)
Confidence: 82.5%
Accuracy: 78.5%
```

### If You See This ✅:
- Demo data is working
- Frontend is rendering correctly
- Ready to connect Google Sheets

### If You See Error ❌:
- Check console for error messages
- See troubleshooting section below

---

## ✅ Test 4: Test Google Sheets Connection

### Step A: Create Test Google Sheet

1. Go to Google Sheets: https://sheets.google.com/
2. Create new sheet called "StockLens Pro - Test"
3. Create a sheet named "Experts Recommendations"
4. Add headers (Row 1):
   ```
   Company | Ticker | Signal | Term | Entry Price | Target Price | Expert | Rating | Confidence % | Accuracy %
   ```

5. Add sample data (Row 2):
   ```
   Apple Inc | AAPL | BUY | Short Term | 150.00 | 165.00 | Test Analyst | 5 | 85 | 80
   ```

6. Share sheet and copy URL

### Step B: Update app.py

Find this line (around 860):
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

Replace with your test sheet URL:
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/YOUR_TEST_SHEET_ID/edit"
```

### Step C: Restart Streamlit

```bash
# Stop current app (Ctrl+C)
# Then restart
streamlit run app.py
```

### Step D: Check Results

Navigate to Tab 3 and verify:
- ✅ Your test data appears
- ✅ AAPL recommendation shows
- ✅ Entry/Target prices correct
- ✅ Expert name shows "Test Analyst"
- ✅ 5 stars display

### Troubleshooting Google Sheets Connection:

#### Error: "Could not fetch from Google Sheets"

**Check 1: Sheet Name**
- Go to Google Sheet
- Is the tab named exactly **"Experts Recommendations"**?
- Column headers must be EXACT (case-sensitive)

**Check 2: Firebase Credentials**
- File should exist: `stocklenspro-firebase-adminsdk-fbsvc-7cf877918e.json`
- In same directory as `app.py`
- Check file is valid JSON

**Check 3: URL Format**
- URL should be: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit`
- NOT: `https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0`
- NOT: Just the sheet ID

**Check 4: Sheet Sharing**
- Click **Share** on Google Sheet
- Make sure it's not "Restricted"
- Set to "Anyone with the link" → "Viewer"

**Check 5: gspread Package**
- Install: `pip install gspread`
- Check: `pip list | grep gspread`

---

## ✅ Test 5: Test Multiple Recommendations

### Create More Test Data:

Add these rows to your Google Sheet:

```
Tesla Inc | TSLA | SELL | Short Term | 250.00 | 220.00 | Bearish Analyst | 4 | 75 | 72
Microsoft Corp | MSFT | BUY | Medium Term | 380.00 | 450.00 | Growth Analyst | 5 | 88 | 85
Google | GOOGL | BUY | Long Term | 140.00 | 200.00 | Tech Specialist | 5 | 90 | 87
```

### Expected Result:
- ✅ All 4 recommendations appear as cards
- ✅ Multiple cards scroll horizontally/vertically
- ✅ Each card displays independently
- ✅ No overlapping or formatting issues

---

## ✅ Test 6: Test Calculations

### Verify Profit Left Calculation:

**Manual Check:**
- Go to Tab 3 (SEBI Experts)
- Look at first expert card
- Entry Price: 150.00
- Target Price: 165.00
- Profit Left % should be: `(165 - current_price) / current_price * 100`

### Example:
If current price of AAPL is 160:
```
Profit Left = (165 - 160) / 160 * 100 = 3.125%
```

**Verify This in App:**
- ✅ Matches calculation
- ✅ Shows as positive/negative
- ✅ Color changes (green if positive, red if negative)

---

## ✅ Test 7: Test Visual Elements

### Check These Visuals:

✅ **Color Coding:**
- BUY cards have TEAL borders (🟢)
- SELL cards have RED borders (🔴)

✅ **Star Ratings:**
- 5 stars: ⭐⭐⭐⭐⭐
- 4 stars: ⭐⭐⭐⭐☆
- 3 stars: ⭐⭐⭐☆☆

✅ **Progress Bar:**
- Bar fills from entry price to current price
- Color gradient from signal color to purple
- Shows entry → current → target positions

✅ **Mobile Responsive:**
- Try resizing browser window
- Cards should stack on mobile
- Text should remain readable

---

## ✅ Test 8: Test Performance

### Add 50+ Recommendations:

1. In your Google Sheet, add 50+ rows of data
2. Run app and check Tab 3

### Check Performance:
- ⏱️ Page loads within 3 seconds
- 📱 No freezing or lag
- 💾 App responsive while scrolling

**If slow:** Check if caching is working (ttl=600 seconds)

---

## ✅ Test 9: Test Different Tickers

### Modify Main App:

1. Go to top of app
2. Change search ticker to different stocks:
   - AAPL (Apple)
   - MSFT (Microsoft)
   - GOOGL (Google)
   - TSLA (Tesla)
   - TCS (Tata Consultancy)
   - RELIANCE.NS (Reliance)

### Verify Tab 3 Updates:
- ✅ Recommendations still load
- ✅ Profit left % recalculates
- ✅ Progress bar updates
- ✅ Colors/styling consistent

---

## ✅ Test 10: Test Error Scenarios

### Test 1: Wrong Sheet URL
```python
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/WRONG_ID/edit"
```
**Expected:** Shows demo data with warning message ✅

### Test 2: Wrong Sheet Name
Sheet tab: "Expert Data" (instead of "Experts Recommendations")
**Expected:** Falls back to demo data ✅

### Test 3: Missing Column Headers
Remove "Confidence %" column
**Expected:** Still loads but that field shows as empty ✅

### Test 4: Invalid Number Format
Entry Price: "abc" (instead of number)
**Expected:** App doesn't crash, shows error or 0 ✅

---

## 📊 Testing Checklist

- [ ] App starts without errors
- [ ] Tab 3 loads without errors
- [ ] Demo data displays correctly
- [ ] Google Sheet connection works
- [ ] Multiple recommendations display
- [ ] Profit % calculations correct
- [ ] Star ratings display
- [ ] Confidence % shows
- [ ] Accuracy % shows
- [ ] Colors are correct (🟢 BUY, 🔴 SELL)
- [ ] Progress bars fill correctly
- [ ] Mobile responsive
- [ ] Performance is acceptable
- [ ] Different tickers work
- [ ] Error handling works

---

## 🎯 What To Test Next

After passing all tests:

1. **Test with Real Data:**
   - Add actual SEBI expert recommendations
   - Test with real stock prices

2. **Test with Live Updates:**
   - Modify Google Sheet
   - See app update (within 10 minutes)

3. **Test User Experience:**
   - Show to test users
   - Get feedback on design

4. **Test Data Validation:**
   - Add invalid data
   - Verify app handles gracefully

---

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Could not fetch from Google Sheets" | Check sheet name, URL, and credentials |
| Demo data shows instead of real data | Verify Google Sheet connection |
| Prices not calculating correctly | Check if Entry/Target are numbers |
| Stars not showing | Rating should be 1-5, not text |
| Very slow to load | Clear Streamlit cache, reduce rows |
| Cards cut off on mobile | Check responsive design settings |

---

## 📞 Debug Mode

To enable detailed logging:

1. Open `app.py`
2. Add after imports:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

3. Run app:
   ```bash
   streamlit run app.py --logger.level=debug
   ```

4. Check terminal for detailed logs

---

## ✅ Final Verification

Before going live:

- [ ] All tests passed
- [ ] Google Sheets connected
- [ ] Demo data works as fallback
- [ ] Calculations correct
- [ ] Design looks good
- [ ] Mobile responsive
- [ ] Performance acceptable
- [ ] No error messages
- [ ] Documentation clear

---

**Ready for production! 🚀**

Need help? Check GOOGLE_SHEETS_SETUP.md for detailed setup instructions.
