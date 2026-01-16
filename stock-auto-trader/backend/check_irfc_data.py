from database import SessionLocal
from models import Stock, Candle, TimeFrame

db = SessionLocal()

# Check IRFC
irfc_stock = db.query(Stock).filter(Stock.symbol == 'IRFC.NS').first()
if irfc_stock:
    print(f'Stock: {irfc_stock.symbol} - {irfc_stock.name} (ID: {irfc_stock.id})')
    # Get latest candle
    candle = db.query(Candle).filter(
        Candle.stock_id == irfc_stock.id,
        Candle.timeframe == TimeFrame.D1
    ).order_by(Candle.timestamp.desc()).first()
    if candle:
        print(f'  Latest 1D: {candle.timestamp} Close={candle.close}')
else:
    print('IRFC.NS not found')

# Check ETHUSDT
eth_stock = db.query(Stock).filter(Stock.symbol == 'ETHUSDT').first()
if eth_stock:
    print(f'\nStock: {eth_stock.symbol} - {eth_stock.name} (ID: {eth_stock.id})')
    candle = db.query(Candle).filter(
        Candle.stock_id == eth_stock.id,
        Candle.timeframe == TimeFrame.D1
    ).order_by(Candle.timestamp.desc()).first()
    if candle:
        print(f'  Latest 1D: {candle.timestamp} Close={candle.close}')
else:
    print('ETHUSDT not found')
