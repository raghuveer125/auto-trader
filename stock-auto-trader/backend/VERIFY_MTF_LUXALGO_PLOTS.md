# Verification Guide: MTF LuxAlgo 5th Indicator Plots

## ✅ Step 1: Verify Database Migration

Check if the new columns exist:

```bash
cd stock-auto-trader/backend
sqlite3 trading.db "PRAGMA table_info(indicator_values);" | grep -E "(volatility_score|market_structure|trend)"
```

**Expected output:** You should see the new columns listed.

---

## ✅ Step 2: Start Backend (if not running)

```bash
cd stock-auto-trader/backend
source venv/bin/activate
python main.py
```

**Expected output:** `Uvicorn running on http://0.0.0.0:8000`

---

## ✅ Step 3: Sync Data and Calculate Indicators

```bash
# Sync BTCUSDT 1d candles and calculate indicators
curl -X POST "http://localhost:8000/candles/BTCUSDT/sync?timeframe=1d"
```

**Expected output:** JSON with sync stats showing indicators were calculated.

---

## ✅ Step 4: Verify Indicator Data is Stored

```bash
# Check if MTF_LUXALGO_5TH indicators are stored
curl -s "http://localhost:8000/indicators/BTCUSDT?timeframe=1d&strategy=MTF_LUXALGO_5TH&limit=5" | python3 -m json.tool | head -50
```

**Expected output:** JSON with:
- `candles` array
- `indicators.MTF_LUXALGO_5TH` object containing:
  - `timestamps` array
  - `volatility_score` array
  - `market_structure` array
  - `trend` array
  - `pattern_sequence` array
  - etc.

---

## ✅ Step 5: Check Latest Signal

```bash
curl -s "http://localhost:8000/signals/BTCUSDT?timeframe=1d&strategy=MTF_LUXALGO_5TH" | python3 -m json.tool
```

**Expected output:** Signal with all indicator values including:
```json
{
  "indicators": {
    "volatility_score": 0.9168,
    "market_structure": "HH",
    "trend": "Bullish",
    "pattern_sequence": "HH → HL",
    "pivot_swing_high": 148.50,
    "pivot_swing_low": 138.50,
    ...
  }
}
```

---

## ✅ Step 6: Verify Frontend Display

1. **Open frontend:** http://localhost:5173
2. **Select symbol:** BTCUSDT
3. **Select strategy:** MTF_LUXALGO_5TH
4. **Check indicator panel:** Should show all values
5. **Check chart:** Should show swing high/low markers

---

## 🐛 Troubleshooting

### Issue: No indicator data returned

**Solution:**
```bash
# Force recalculation by deleting existing indicators
sqlite3 trading.db "DELETE FROM indicator_values WHERE strategy='MTF_LUXALGO_5TH';"

# Re-sync
curl -X POST "http://localhost:8000/candles/BTCUSDT/sync?timeframe=1d"
```

### Issue: Chart shows no markers

**Check browser console (F12):**
- Look for JavaScript errors
- Check if `indicators` object has data
- Verify `timestamps` array matches candle count

### Issue: "Column not found" error

**Re-run migration:**
```bash
python3 migrations/add_mtf_luxalgo_5th_columns.py
```

---

## 📊 What Should Be Visible

### Indicator Panel (Top Section)
- ✅ Volatility Score: 1.73
- ✅ Internal Length: 5
- ✅ Swing Length: 50
- ✅ Market Structure: HH / HL / LH / LL / None
- ✅ Trend: Bullish / Bearish / Neutral
- ✅ Pattern Sequence: "HH → HL → HH"
- ✅ Pivot values (when detected)

### Chart (Bottom Section)
- ✅ Candlestick chart
- ✅ Red arrow markers (↓) with "sH: XXX.XX" for swing highs
- ✅ Green arrow markers (↑) with "sL: XXX.XX" for swing lows

---

## 🎯 Quick Test Command

Run this all-in-one test:

```bash
echo "=== Testing MTF_LUXALGO_5TH Indicators ===" && \
curl -X POST "http://localhost:8000/candles/BTCUSDT/sync?timeframe=1d" 2>&1 | grep -q "success" && \
echo "✓ Sync successful" && \
curl -s "http://localhost:8000/signals/BTCUSDT?timeframe=1d&strategy=MTF_LUXALGO_5TH" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✓ Signal:', d['signals'][0]['signal']); print('✓ Market Structure:', d['signals'][0]['indicators'].get('market_structure', 'N/A')); print('✓ Trend:', d['signals'][0]['indicators'].get('trend', 'N/A'))" && \
echo "=== All tests passed! ==="
```

**Expected output:**
```
=== Testing MTF_LUXALGO_5TH Indicators ===
✓ Sync successful
✓ Signal: HOLD
✓ Market Structure: HH
✓ Trend: Bullish
=== All tests passed! ===
```

