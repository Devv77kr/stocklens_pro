# ⚡ StockLens Pro - SEBI Experts - Quick Reference Card

## 🎯 **5-Minute Quick Start**

```
1. pip install gspread
2. Create Google Sheet named "StockLens Pro"
3. Add sheet tab: "Experts Recommendations"
4. Add headers: Company | Ticker | Signal | Term | Entry Price | Target Price | Expert | Rating | Confidence % | Accuracy %
5. Add sample data (see below)
6. Share sheet → Copy URL
7. Update app.py line ~860 with your URL
8. Run: streamlit run app.py
9. Go to Tab 3
10. See recommendations! 🎉
```

---

## 📊 **Sample Google Sheet Data**

```
Company | Ticker | Signal | Term | Entry Price | Target Price | Expert | Rating | Confidence % | Accuracy %
Tata Consultancy Services | TCS | BUY | Short Term | 2080 | 2300 | Expert 1 | 5 | 82.5 | 78.5
Reliance Industries | RELIANCE.NS | BUY | Medium Term | 2900 | 3500 | Expert 2 | 5 | 88 | 85
Infosys | INFY | SELL | Short Term | 1850 | 1650 | Expert 3 | 4 | 75 | 72
```

---

## 🔑 **Key Commands**

| Command | Purpose |
|---------|---------|
| `pip install gspread` | Install Google Sheets library |
| `pip install -r requirements.txt` | Install all dependencies |
| `streamlit run app.py` | Start the app |
| `streamlit cache clear` | Clear cache if data not updating |

---

## 📱 **What You Get**

### **Expert Card Shows:**
- ✅ Company name & ticker
- ✅ 🟢 BUY or 🔴 SELL signal
- ✅ Entry price (recommendation)
- ✅ Target price (profit goal)
- ✅ Profit Left % (real-time)
- ✅ ⭐ Expert rating (1-5)
- ✅ Confidence % (expert certainty)
- ✅ Accuracy % (historical success)
- ✅ Progress bar (entry to target)

### **Additional Sections:**
- ✅ Growth Metrics (1D, 1W, 1M, 3M, 1Y)
- ✅ Returns Comparison (Stock vs Industry)
- ✅ Quick Guide explanations

---

## 🔗 **Google Sheets URL Format**

**Correct:**
```
https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit
```

**Where to add in app.py (line ~860):**
```python
GOOGLE_SHEETS_URL = "YOUR_URL_HERE"
```

---

## ✅ **Verification Checklist**

- [ ] gspread installed (`pip list | grep gspread`)
- [ ] Google Sheet created
- [ ] Sheet named "Experts Recommendations"
- [ ] Headers exact (Company, Ticker, Signal, Term, Entry Price, Target Price, Expert, Rating, Confidence %, Accuracy %)
- [ ] Data added with numbers (not text)
- [ ] Sheet shared "Anyone with the link"
- [ ] URL copied correctly
- [ ] app.py updated with URL
- [ ] App starts: `streamlit run app.py`
- [ ] Tab 3 shows data
- [ ] Calculations look correct

---

## 🚨 **Common Issues & Quick Fixes**

| Issue | Fix |
|-------|-----|
| "Could not fetch from Google Sheets" | Check sheet name = "Experts Recommendations" (exact case) |
| Import error gspread | Run: `pip install gspread` |
| Data not updating | Restart app: Press Ctrl+C, then `streamlit run app.py` |
| Wrong calculations | Check if Entry/Target are NUMBERS not text |
| Stars not showing | Rating should be 1-5, not text |
| Slow to load | Google Sheet has too many rows (reduce to < 50) |

---

## 📋 **Column Reference**

| Column | Type | Example | Required? |
|--------|------|---------|-----------|
| Company | Text | Tata Consultancy Services | ✅ Yes |
| Ticker | Text | TCS | ✅ Yes |
| Signal | Text | BUY or SELL | ✅ Yes |
| Term | Text | Short Term | ✅ Yes |
| Entry Price | Number | 2080.00 | ✅ Yes |
| Target Price | Number | 2300.00 | ✅ Yes |
| Expert | Text | Expert Analyst 1 | ✅ Yes |
| Rating | Number | 5 (1-5) | ❌ Optional (default: 5) |
| Confidence % | Number | 82.5 (0-100) | ❌ Optional (default: 75) |
| Accuracy % | Number | 78.5 (0-100) | ❌ Optional (default: 0) |

---

## 🎯 **Feature Walkthrough**

### **Entry & Target Prices**
```
Entry = Buy recommendation (where to enter)
Target = Profit target (where to sell)
Example: Entry ₹2080 → Target ₹2300 = 10.5% profit potential
```

### **Profit Left %**
```
Automatically calculated from:
Profit Left = (Target - Current Price) / Current Price × 100

Example: Target ₹2300, Current ₹2100
Profit Left = (2300 - 2100) / 2100 × 100 = 9.52%
```

### **Star Rating (⭐)**
```
⭐⭐⭐⭐⭐ = 5 stars (Very confident)
⭐⭐⭐⭐☆ = 4 stars (Confident)
⭐⭐⭐☆☆ = 3 stars (Moderate confidence)
```

### **Confidence %**
```
82.5% = Expert is 82.5% confident in this recommendation
Higher = More likely to be accurate
```

### **Accuracy %**
```
78.5% = Expert's past recommendations were correct 78.5% of the time
Higher = More reliable expert
```

---

## 📱 **Tab Navigation**

```
Tab 1: Price Overview
Tab 2: Technical Indicators (Easy to understand)
Tab 3: ← YOU ARE HERE - SEBI Expert Recommendations
Tab 4: Risk Analysis
Tab 5: AI Forecast
Tab 6: Portfolio Compare
Tab 7: Financials
Tab 8: News & Sentiment
```

---

## ⚙️ **Code Location Reference**

| Component | Location | Line # |
|-----------|----------|--------|
| Google Sheets integration | app.py | ~55-85 |
| Google Sheets URL | app.py | ~860 |
| Demo data fallback | app.py | ~870-900 |
| Expert card rendering | app.py | ~910-1000 |
| Growth metrics | app.py | ~1000-1040 |
| Returns comparison | app.py | ~1040-1080 |

---

## 🚀 **Launch Commands**

```bash
# Install package
pip install gspread

# Start app
streamlit run app.py

# Clear cache if needed
streamlit cache clear

# Run with debug
streamlit run app.py --logger.level=debug

# Check installation
python -c "import gspread; print('gspread OK')"
```

---

## 📞 **Getting Help**

### **Quick Answers:**
1. See **GOOGLE_SHEETS_SETUP.md** (setup issues)
2. See **TESTING_GUIDE.md** (testing/verification)
3. See **SETUP_COMPLETE.md** (overview & features)

### **Error Messages:**
- Check terminal output
- Enable debug mode: `streamlit run app.py --logger.level=debug`
- Look for red error text in browser

### **Performance Issues:**
- Reduce Google Sheet rows (< 50)
- Clear cache: `streamlit cache clear`
- Restart app: Ctrl+C → `streamlit run app.py`

---

## 💡 **Tips & Tricks**

### **Pro Tips:**
- 💰 Sort recommendations by Profit Left % for quick wins
- ⭐ Sort by Star Rating for most reliable experts
- 📊 Check Accuracy % for proven experts
- 🎯 Use Short Term for quick trades, Long Term for investments
- 📱 Mobile friendly - works great on phone!

### **Best Practices:**
- ✅ Update Google Sheet weekly with new recommendations
- ✅ Monitor which experts have highest accuracy
- ✅ Remove expired recommendations (old dates)
- ✅ Add notes in Expert column (e.g., "Expert: John (Bullish)")
- ✅ Test with small amounts first

---

## 📈 **Expected Performance**

| Metric | Target | Actual |
|--------|--------|--------|
| App Load Time | < 3s | ⏱️ Depends on internet |
| Tab 3 Load Time | < 2s | ⏱️ With cache |
| Data Update Frequency | Real-time | 10 min (cached) |
| Calculation Accuracy | 100% | ✅ Verified |
| Mobile Responsive | Yes | ✅ Yes |

---

## 🎉 **Success Indicators**

You're done when you see:
- ✅ Tab 3 loads without errors
- ✅ Expert cards display correctly
- ✅ Profit % calculates properly
- ✅ Star ratings show
- ✅ Confidence & Accuracy display
- ✅ All colors correct (🟢 BUY, 🔴 SELL)
- ✅ Growth metrics section works
- ✅ Returns comparison table shows data
- ✅ Mobile view looks good
- ✅ No warning/error messages

---

## 📊 **Sample Output**

```
SEBI Registered Experts' Recommendation 👨‍💼

📊 Expert Analyst 1
Tata Consultancy Services (TCS)
Ticker: TCS

🟢 BUY · Short Term
⭐⭐⭐⭐⭐

│ Entry Price: ₹2,080.00  │  Target Price: ₹2,300.00  │  Confidence: 82.5%    │
│ Profit Left: +10.50%    │                           │  Accuracy: 78.5%     │

[████████░░░░░░░░░] Progress Bar
Entry: ₹2,080  Current: ₹2,100  Target: ₹2,300
```

---

## ⏱️ **Timeline**

| Task | Time | Done? |
|------|------|-------|
| Read this file | 5 min | |
| Install gspread | 2 min | |
| Create Google Sheet | 10 min | |
| Add sample data | 5 min | |
| Update app.py | 1 min | |
| Run & test | 10 min | |
| **Total** | **~35 min** | |

---

## ✨ **What's Next?**

After setup:
1. Add real expert recommendations
2. Monitor recommendation accuracy
3. Gather user feedback
4. Optimize based on results
5. Scale to more experts

---

**Good luck! You've got this! 🚀📈💰**
