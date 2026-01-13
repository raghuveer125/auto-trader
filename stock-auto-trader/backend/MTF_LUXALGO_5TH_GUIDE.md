# MTF_LUXALGO_5TH Strategy Guide

## Overview
The MTF_LUXALGO_5TH strategy is a comprehensive Smart Money Concepts (SMC) trading system converted from TradingView's Pine Script. It combines multiple advanced techniques:

- **Market Structure** (BOS, CHoCH, CHoCH+)
- **Order Blocks** (Demand/Supply zones)
- **Fair Value Gaps** (FVG)
- **Accumulation/Distribution Zones**
- **Adaptive Pivot Detection**

## Features Implemented

### 1. Adaptive Pivot Detection
- **Auto Mode**: Automatically adjusts pivot length based on volatility
- **Dynamic Mode**: Uses ATR-based adaptive length
- **Manual Mode**: Fixed swing length (default: 10)

### 2. Market Structure Detection
- **BOS (Break of Structure)**: Confirms trend continuation
- **CHoCH (Change of Character)**: Signals potential reversal
- **CHoCH+**: Strong reversal signal
- **Pattern Sequences**: HH, HL, LL, LH tracking

### 3. Order Blocks (OB)
- Tracks up to 5 bullish and 5 bearish order blocks
- Mitigation detection (Close or Wick based)
- Volume-weighted zones
- Automatic cleanup of mitigated blocks

### 4. Fair Value Gaps (FVG)
- Detects imbalances in price action
- Tracks up to 5 bullish and 5 bearish FVGs
- Mitigation tracking (Wick or Close based)
- Automatic cleanup

### 5. Accumulation/Distribution Zones
- **Fast Mode**: 4-pivot detection (L-H-L-H or H-L-H-L)
- **Slow Mode**: 6-pivot detection for higher confidence
- Breakout/Breakdown detection
- Retest confirmation signals

## Signal Strength Hierarchy

1. **85%** - Zone Breakouts (Accumulation/Distribution)
2. **70%** - Market Structure BOS
3. **65%** - Market Structure CHoCH
4. **60%** - Order Block Touches
5. **55%** - Trend Continuation

## Configuration Parameters

```python
{
    "swing_length": 10,          # Pivot detection length (5-50)
    "ob_num": 5,                 # Max Order Blocks (1-10)
    "ob_mitigation": "Close",    # OB mitigation: "Close" or "Wick"
    "fvg_num": 5,                # Max FVGs (1-10)
    "fvg_src": "Wick",           # FVG source: "Wick" or "Close"
    "show_acc_dist_zone": true,  # Enable zone detection
    "zone_mode": "Fast"          # Zone mode: "Fast" or "Slow"
}
```

## Frontend Visualization

### Chart Overlays
- **Order Blocks**: Green (bullish) and Red (bearish) zones
- **FVGs**: Blue (bullish) and Orange (bearish) gaps
- **Swing Pivots**: Markers showing swing highs/lows
- **Market Structure**: BOS/CHoCH labels

### Dashboard (Top-Right)
- Market Structure (Trend, Structure Type, Pattern)
- Active Order Blocks (Bullish/Bearish)
- Active Fair Value Gaps (Bullish/Bearish)

## API Endpoints

### Get Signal
```bash
GET /signals/BTCUSDT?timeframe=1d&strategy=MTF_LUXALGO_5TH
```

### Get Indicators
```bash
GET /indicators/BTCUSDT?timeframe=1d&strategy=MTF_LUXALGO_5TH&limit=100
```

### Update Settings
```bash
POST /strategy-settings/MTF_LUXALGO_5TH
{
    "swing_length": 15,
    "ob_num": 3
}
```

## Usage Tips

1. **Higher Timeframes**: Use 1d or 4h for swing trading
2. **Lower Timeframes**: Use 15m or 1h for intraday
3. **Zone Signals**: Highest priority - wait for retest confirmation
4. **OB Touches**: Good entry points in trending markets
5. **Structure Breaks**: Confirm with volume and momentum

## Testing

Run the test suite:
```bash
python test_complete_strategy.py
```

## Troubleshooting

### No Signals Generated
- Ensure sufficient data (minimum 100 candles)
- Check if market is ranging (no clear structure)
- Verify settings are not too restrictive

### Missing Visualizations
- Refresh the frontend
- Check browser console for errors
- Verify backend is returning indicators data

## Next Steps

1. Backtest on historical data
2. Fine-tune parameters for specific symbols
3. Add risk management rules
4. Implement multi-timeframe confirmation

