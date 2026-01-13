#!/usr/bin/env python3
"""Test Order Block detection"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Candle, Indicator
from sqlalchemy import desc

print("Testing Order Block Implementation")
print("=" * 60)

db = SessionLocal()

try:
    # Get latest indicator for BTCUSDT 1d
    indicator = db.query(Indicator).join(Candle).filter(
        Candle.symbol == "BTCUSDT",
        Candle.timeframe == "1d",
        Indicator.strategy == "MTF_LUXALGO_5TH"
    ).order_by(desc(Candle.timestamp)).first()
    
    if indicator:
        print(f"\n✅ Found MTF_LUXALGO_5TH indicator")
        print(f"Timestamp: {indicator.candle.timestamp}")
        print(f"Market Structure: {indicator.market_structure}")
        print(f"Trend: {indicator.trend}")
        
        print(f"\n📊 Bullish Order Block (Demand Zone):")
        if indicator.ob_bull_top:
            print(f"  Top: {indicator.ob_bull_top}")
            print(f"  Btm: {indicator.ob_bull_btm}")
            print(f"  Avg: {indicator.ob_bull_avg}")
            print(f"  Volume: {indicator.ob_bull_volume}")
            print(f"  Time: {indicator.ob_bull_time}")
            print(f"  Mitigated: {indicator.ob_bull_mitigated}")
        else:
            print(f"  No bullish OB detected")
        
        print(f"\n📊 Bearish Order Block (Supply Zone):")
        if indicator.ob_bear_top:
            print(f"  Top: {indicator.ob_bear_top}")
            print(f"  Btm: {indicator.ob_bear_btm}")
            print(f"  Avg: {indicator.ob_bear_avg}")
            print(f"  Volume: {indicator.ob_bear_volume}")
            print(f"  Time: {indicator.ob_bear_time}")
            print(f"  Mitigated: {indicator.ob_bear_mitigated}")
        else:
            print(f"  No bearish OB detected")
    else:
        print("\n❌ No MTF_LUXALGO_5TH indicators found")
        print("Run: curl -X POST 'http://localhost:8000/candles/BTCUSDT/sync?timeframe=1d'")

finally:
    db.close()

print("\n" + "=" * 60)

