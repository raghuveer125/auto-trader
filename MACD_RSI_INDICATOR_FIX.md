# MACD & RSI Indicator Plotting Fix

## Problem
MACD and RSI indicators were not displaying on the strategy cards in the dashboard. The charts showed only candlesticks with no indicator overlays.

## Root Cause
The indicators had never been calculated and stored in the database for the stocks. When the frontend requested indicator data via the `/indicators` endpoint, it returned empty arrays because no `IndicatorValue` records existed in the database.

## Solution

### Backend Changes
1. **Added new endpoint** `/indicators/{symbol}/calculate` - Calculates indicators for existing candles without needing to sync/fetch new data
   - File: [backend/main.py](stock-auto-trader/backend/main.py#L369-L403)
   - Endpoint: `POST /indicators/{symbol}/calculate?timeframe=1d`
   - Response: `{stored: N, strategies: [...]}`

### Frontend Changes
1. **Updated API client** - Added `calculate()` method to `indicatorsAPI`
   - File: [frontend/src/services/api.js](frontend/src/services/api.js)

2. **Auto-calculation in StrategyCard** - When indicators are empty, automatically trigger calculation before rendering chart
   - File: [frontend/src/components/StrategyCard.jsx](frontend/src/components/StrategyCard.jsx#L209-L276)
   - Logic: If candles exist but indicators are missing, call `/indicators/{symbol}/calculate` and retry

## How It Works

### For Existing Stocks (No Manual Action Required)
1. User opens dashboard and views a strategy card
2. Frontend requests indicators via `/indicators` endpoint
3. If candles exist but indicators are empty:
   - Frontend automatically calls `/indicators/{symbol}/calculate` to compute them
   - Indicators are now stored in database
   - Frontend retries the indicators request
   - Chart displays with indicator overlays

### Manual Trigger (For Bulk Operations)
```bash
# Calculate indicators for a stock
curl -X POST http://localhost:8000/indicators/TCS.NS/calculate?timeframe=1d

# Response
{
  "symbol": "TCS.NS",
  "timeframe": "1d",
  "stored": 14328,
  "strategies": ["MACD", "RSI", "MA_CROSSOVER", "BOLLINGER", "MTF_EMA", "MTF_LUXALGO_5TH"]
}
```

## Testing

### MACD Indicators
```bash
curl -s "http://localhost:8000/indicators/AAPL?timeframe=1d&strategy=MACD&limit=5" | python3 -m json.tool
# Returns: macd_line, macd_signal, macd_histogram arrays with timestamps
```

### RSI Indicators
```bash
curl -s "http://localhost:8000/indicators/AAPL?timeframe=1d&strategy=RSI&limit=5" | python3 -m json.tool
# Returns: rsi_value array with timestamps
```

## Data Flow (After Fix)

1. **Initial Load**: Dashboard displays empty indicator arrays
2. **Auto-Detection**: Frontend detects missing indicators for displayed timeframe
3. **Auto-Calculate**: POST `/indicators/{symbol}/calculate` triggered
4. **Store**: Indicators calculated and stored in `indicator_values` table
5. **Display**: Chart renders with MACD/RSI/etc. indicator lines/areas

## Files Modified

- [backend/main.py](stock-auto-trader/backend/main.py) - Added `/indicators/{symbol}/calculate` endpoint
- [frontend/src/services/api.js](frontend/src/services/api.js) - Added `indicatorsAPI.calculate()`
- [frontend/src/components/StrategyCard.jsx](frontend/src/components/StrategyCard.jsx) - Added auto-calculation logic

## Benefits

✅ Indicators automatically populate when needed (no manual intervention)
✅ Faster than re-syncing candles (only calculates, doesn't fetch data)
✅ Works for all timeframes (1m, 5m, 15m, 30m, 1h, 2h-5h, 1d)
✅ Supports all strategies (MACD, RSI, MA_CROSSOVER, BOLLINGER, MTF_EMA, MTF_LUXALGO_5TH)
✅ Can be bulk-triggered via API for initialization

## Next Steps (Optional)

1. Add a "Calculate Indicators" button to the stock list for bulk initialization
2. Add indicator calculation to the stock initialization process
3. Schedule periodic indicator updates for all stocks (background job)
