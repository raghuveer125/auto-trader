#!/usr/bin/env python3
"""Test complete MTF_LUXALGO_5TH strategy"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Candle
from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy
import pandas as pd

print("Testing Complete MTF_LUXALGO_5TH Strategy")
print("=" * 70)

db = SessionLocal()

try:
    # Get BTCUSDT 1d candles
    candles = db.query(Candle).filter(
        Candle.symbol == "BTCUSDT",
        Candle.timeframe == "1d"
    ).order_by(Candle.timestamp).limit(300).all()
    
    if len(candles) < 100:
        print(f"❌ Not enough data: {len(candles)} candles")
        exit(1)
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])
    
    print(f"✅ Loaded {len(df)} candles")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    
    # Initialize strategy
    strategy = MTFLuxAlgo5thStrategy()
    
    # Calculate signal
    result = strategy.calculate(df)
    
    print(f"\n📊 Strategy Result:")
    print(f"Signal: {result['signal']}")
    print(f"Strength: {result['strength']}")
    print(f"Reason: {result['reason']}")
    
    indicators = result.get('indicators', {})
    
    print(f"\n📈 Market Structure:")
    print(f"  Trend: {indicators.get('trend', 'N/A')}")
    print(f"  Structure: {indicators.get('market_structure', 'N/A')}")
    print(f"  Sequence: {indicators.get('pattern_sequence', 'N/A')}")
    
    print(f"\n📊 Order Blocks:")
    print(f"  Bullish OB: {indicators.get('ob_bull_top', 'None')}")
    print(f"  Bearish OB: {indicators.get('ob_bear_top', 'None')}")
    
    print(f"\n📊 Fair Value Gaps:")
    print(f"  Bullish FVG: {indicators.get('fvg_bull_top', 'None')}")
    print(f"  Bearish FVG: {indicators.get('fvg_bear_top', 'None')}")
    
    print(f"\n📊 Pivots:")
    print(f"  Swing High: {indicators.get('pivot_swing_high', 'None')}")
    print(f"  Swing Low: {indicators.get('pivot_swing_low', 'None')}")
    
    print(f"\n✅ Strategy calculation successful!")

finally:
    db.close()

print("\n" + "=" * 70)

