# LuxAlgo Dashboard Debugging Guide

## Issue: Dashboard Not Loading Data

### Changes Made to Fix

#### 1. Backend Strategy (`backend/strategies/mtf_luxalgo_5th.py`)
**Problem**: MTF trends were using numeric `trend` variable instead of being properly typed.

**Fix**: Ensured all MTF trend values are integers:
```python
"mtf_trends": {
    "1m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
    "3m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
    # ... all 9 timeframes
}
```

#### 2. Frontend Component (`frontend/src/components/LuxAlgoDashboard.jsx`)

**Changes**:
1. Added debug logging to track indicator data:
```javascript
useEffect(() => {
  console.log('LuxAlgoDashboard received indicators:', indicators);
  console.log('MTF Trends:', indicators.mtf_trends);
  console.log('Market Structure:', indicators.market_structure);
  console.log('Order Blocks:', indicators.order_blocks);
}, [indicators]);
```

2. Added "No data" fallback message:
```javascript
const hasData = indicators && Object.keys(indicators).length > 0;

if (!hasData) {
  return (
    <div className="luxalgo-dashboard">
      <div className="luxalgo-dashboard-content">
        <div className="luxalgo-section">
          <p style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
            No LuxAlgo data available. Waiting for strategy calculation...
          </p>
        </div>
      </div>
    </div>
  );
}
```

3. Enhanced trend helpers to handle both string and numeric values:
```javascript
const getTrendClass = (trendValue) => {
  if (trendValue === 1 || trendValue === 'BULLISH' || trendValue === 'Bullish') return 'bullish';
  if (trendValue === -1 || trendValue === 'BEARISH' || trendValue === 'Bearish') return 'bearish';
  return 'neutral';
};
```

## How to Debug

### 1. Check Browser Console
Open the browser console (F12) and look for:
- `LuxAlgoDashboard received indicators:` - Should show the full indicators object
- `MTF Trends:` - Should show the multi-timeframe data
- `Market Structure:` - Should show BOS/CHoCH/None
- `Order Blocks:` - Should show bullish/bearish arrays

### 2. Verify Backend is Running
```bash
curl http://localhost:8000/api/signals/BTCUSDT/MTF_LUXALGO_5TH
```

Should return JSON with:
- `signal`: "BUY", "SELL", or "HOLD"
- `strength`: 0-100
- `reason`: String explanation
- `indicators`: Object with all dashboard fields

### 3. Check Indicator Structure
The indicators object should contain:
```json
{
  "mtf_trends": {
    "1m": {"trend": 1, "pattern": "HH"},
    "3m": {"trend": 1, "pattern": "HH"},
    ...
  },
  "market_structure": "BOS",
  "trend": "Bullish",
  "pattern_sequence": "HH",
  "order_blocks": {
    "bullish": [...],
    "bearish": [...]
  },
  "fvgs": {
    "bullish": [...],
    "bearish": [...]
  },
  "detected_pattern": "None",
  "recent_hhll": "HH @ 123.45",
  "swing_path": "HH-HL-HH",
  "zone_signal": "-",
  "zone_bias": "NEUTRAL",
  "context": "Range / No Edge",
  "confidence": 75,
  "trade_mode": "WAIT",
  ...
}
```

### 4. Test with Sample Data
Run the test script:
```bash
cd stock-auto-trader/backend
python3 test_luxalgo_dashboard.py
```

This will:
- Generate test data
- Run the strategy
- Print all indicator values
- Save sample JSON to `luxalgo_sample_data.json`

### 5. Check Component Integration
Verify the dashboard is being rendered in:
- `StrategyCard.jsx` (line ~481)
- `ChartModal.jsx` (line ~372)

Both should have:
```jsx
{strategy === 'MTF_LUXALGO_5TH' && displaySignal?.indicators && (
  <LuxAlgoDashboard
    indicators={displaySignal.indicators}
    draggable={false}  // or true for ChartModal
  />
)}
```

## Common Issues

### Issue 1: "No LuxAlgo data available" message
**Cause**: Indicators object is empty or undefined
**Solution**: 
- Check if strategy is calculating correctly
- Verify API is returning indicators
- Check browser console for errors

### Issue 2: Trends showing as "-"
**Cause**: MTF trends not in correct format
**Solution**:
- Verify backend returns `mtf_trends` object
- Check trend values are integers (1, -1, 0)
- Verify pattern values are strings

### Issue 3: Order Blocks not showing
**Cause**: Order blocks array is empty or mitigated
**Solution**:
- Check if strategy is detecting order blocks
- Verify `order_blocks.bullish` and `order_blocks.bearish` arrays exist
- Check `mitigated` flag is false

## Testing Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 5173
- [ ] Browser console shows indicator data
- [ ] MTF trends table displays correctly
- [ ] Market structure shows BOS/CHoCH
- [ ] Order blocks display with values
- [ ] FVGs display with values
- [ ] Confidence meter shows percentage
- [ ] Dashboard is draggable in chart modal
- [ ] Dashboard is static in strategy card

## Next Steps

If data is still not loading:
1. Check backend logs: `tail -f logs/backend.log`
2. Check frontend logs: `tail -f logs/frontend.log`
3. Verify database has indicator data
4. Test with different symbols
5. Restart services: `./re-start-services.sh`

