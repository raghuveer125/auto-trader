import sys
sys.path.insert(0, '/Users/bhoomidakshpc/project1/StockAutoTradingVR/auto-trader/stock-auto-trader')

from database import SessionLocal
from models import Stock, TimeFrame
from main import _get_stored_indicator_values

db = SessionLocal()
stock = db.query(Stock).filter(Stock.symbol == "AAPL").first()
if stock:
    try:
        result = _get_stored_indicator_values(db, stock.id, TimeFrame.M1, None, 200)
        print("Success! Result:", result)
    except Exception as e:
        import traceback
        print("Error:", e)
        traceback.print_exc()
else:
    print("Stock not found")
