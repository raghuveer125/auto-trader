#!/usr/bin/env python3
"""Quick script to check if a symbol has data in the database"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Stock, Candle, Indicator, TimeFrame

# Database setup
DATABASE_URL = "sqlite:///./stock_trader.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_symbol(symbol: str):
    """Check if symbol has data"""
    db = SessionLocal()
    
    print(f"\n{'='*60}")
    print(f"Checking data for: {symbol}")
    print(f"{'='*60}")
    
    # Check if stock exists
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
    if not stock:
        print(f"❌ Stock '{symbol}' NOT FOUND in database")
        print(f"\n💡 Solution: Click 'Sync Data Now' button in the UI")
        db.close()
        return
    
    print(f"✅ Stock found: {stock.symbol} - {stock.name}")
    
    # Check candles
    candle_count = db.query(Candle).filter(Candle.stock_id == stock.id).count()
    print(f"\n📊 Candles: {candle_count} total")
    
    if candle_count == 0:
        print(f"❌ No candles found")
        print(f"\n💡 Solution: Click 'Sync Data Now' button in the UI")
        db.close()
        return
    
    # Check candles by timeframe
    print(f"\nCandles by timeframe:")
    for tf in [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30, 
               TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]:
        count = db.query(Candle).filter(
            Candle.stock_id == stock.id,
            Candle.timeframe == tf
        ).count()
        if count > 0:
            print(f"  {tf.value}: {count} candles")
    
    # Check indicators
    indicator_count = db.query(Indicator).filter(Indicator.stock_id == stock.id).count()
    print(f"\n📈 Indicators: {indicator_count} total")
    
    if indicator_count == 0:
        print(f"⚠️  No indicators calculated yet")
        print(f"\n💡 Indicators are calculated when you fetch signals")
    else:
        # Check indicators by strategy
        from sqlalchemy import func
        strategies = db.query(Indicator.strategy, func.count(Indicator.id)).filter(
            Indicator.stock_id == stock.id
        ).group_by(Indicator.strategy).all()
        
        print(f"\nIndicators by strategy:")
        for strategy, count in strategies:
            print(f"  {strategy}: {count} records")
    
    # Check latest candle
    latest_candle = db.query(Candle).filter(
        Candle.stock_id == stock.id,
        Candle.timeframe == TimeFrame.D1
    ).order_by(Candle.timestamp.desc()).first()
    
    if latest_candle:
        print(f"\n📅 Latest 1D candle: {latest_candle.timestamp}")
        print(f"   Close: ${latest_candle.close:.2f}")
    
    print(f"\n{'='*60}")
    print(f"✅ Symbol has data - signals should be available")
    print(f"{'='*60}\n")
    
    db.close()

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    check_symbol(symbol)

