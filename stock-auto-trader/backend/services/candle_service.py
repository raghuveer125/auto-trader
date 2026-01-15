import requests
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from models import Stock, Candle, TimeFrame
from services.binance_service import is_crypto_symbol, fetch_binance_candles
from services.google_finance_service import google_finance_available
from concurrent.futures import ThreadPoolExecutor, as_completed


# Timeframe mapping for Yahoo Finance API
# Note: Yahoo only supports: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
# 2h, 3h, 4h, 5h are NOT directly supported - we can only use available intervals
TIMEFRAME_MAP = {
    TimeFrame.M1: {"interval": "1m", "range": "7d"},
    TimeFrame.M5: {"interval": "5m", "range": "60d"},
    TimeFrame.M15: {"interval": "15m", "range": "60d"},
    TimeFrame.M30: {"interval": "30m", "range": "60d"},
    TimeFrame.H1: {"interval": "1h", "range": "730d"},
    TimeFrame.D1: {"interval": "1d", "range": "10y"},
}

# Timeframes that require resampling from 1h data
RESAMPLE_TIMEFRAMES = {
    TimeFrame.H2: "2h",
    TimeFrame.H3: "3h",
    TimeFrame.H4: "4h",
    TimeFrame.H5: "5h",
}

def yahoo_symbol(symbol: str) -> str:
    return "^BSESN" if symbol.upper() == "SENSEX" else symbol

def get_or_create_stock(db: Session, symbol: str) -> Stock:
    """Get stock from DB or create if not exists (thread-safe)"""
    symbol = symbol.upper().strip()
    stock = db.query(Stock).filter(Stock.symbol == symbol).first()

    if not stock:
        # Fetch name from Yahoo Finance API (skip for indices like SENSEX)
        try:
            if symbol == "SENSEX":
                name = "BSE Sensex"
            else:
                url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}"
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, headers=headers, timeout=10)
                data = response.json()
                name = data.get("quotes", [{}])[0].get("shortname", symbol)
        except Exception:
            name = symbol


        try:
            stock = Stock(symbol=symbol, name=name)
            db.add(stock)
            db.commit()
            db.refresh(stock)
        except Exception as e:
            # Handle race condition: another thread may have created it
            db.rollback()
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                raise e  # Re-raise if it's a different error

    return stock


def get_latest_candle_timestamp(db: Session, stock_id: int, timeframe: TimeFrame) -> Optional[datetime]:
    """Get the timestamp of the latest candle in DB for incremental sync"""
    latest = (
        db.query(Candle)
        .filter(Candle.stock_id == stock_id, Candle.timeframe == timeframe)
        .order_by(Candle.timestamp.desc())
        .first()
    )
    if latest:
        print(f"📅 Latest candle in DB: {latest.timestamp} for timeframe {timeframe.value}")
    return latest.timestamp if latest else None


def fetch_candles_from_yahoo_api(
    symbol: str,
    timeframe: TimeFrame,
    start_timestamp: Optional[int] = None
) -> List[Dict]:

    # Use Binance for crypto (unchanged)
    if is_crypto_symbol(symbol):
        return fetch_binance_candles(symbol, timeframe, start_timestamp)

    # ✅ Google Finance FIRST (availability gate, no candle fetch)
    if symbol.upper() == "SENSEX" and timeframe == TimeFrame.M1:
        from services.google_finance_service import fetch_google_candles
        candles = fetch_google_candles(symbol, timeframe, start_timestamp)
        if candles:
            return candles

    # Check if this timeframe needs resampling (for non-crypto via Yahoo)
    if timeframe in RESAMPLE_TIMEFRAMES:
        return _fetch_and_resample_candles(symbol, timeframe, start_timestamp)

    config = TIMEFRAME_MAP.get(timeframe)
    if not config:
        raise Exception(f"Unsupported timeframe: {timeframe.value}")
    
    # Yahoo Finance API endpoint
    y_symbol = yahoo_symbol(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{y_symbol}"

    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    params = {
        "interval": config["interval"],
        "range": config["range"],
    }
    
    # If we have a start timestamp, use period1/period2 instead of range
    if start_timestamp:
        params.pop("range", None)
        params["period1"] = start_timestamp
        params["period2"] = int(datetime.now().timestamp())
    
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Yahoo API returned status {response.status_code}")
    
    data = response.json()
    
    # Check for errors
    if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
        error = data.get("chart", {}).get("error", {})
        raise Exception(f"Yahoo API error: {error.get('description', 'Unknown error')}")
    
    result = data["chart"]["result"][0]
    timestamps = result.get("timestamp", [])
    
    if not timestamps:
        return []
    
    # Validate quote data exists before accessing
    indicators = result.get("indicators", {})
    quotes = indicators.get("quote", [])
    if not quotes or len(quotes) == 0:
        return []
    
    quote = quotes[0]
    
    candles = []
    for i, ts in enumerate(timestamps):
        # Skip if any OHLC value is None
        if any(quote[k][i] is None for k in ["open", "high", "low", "close"]):
            continue

        # Use UTC timestamp for consistency across all data sources
        # Yahoo Finance provides timestamps in UTC
        candle_ts = datetime.utcfromtimestamp(ts).replace(microsecond=0)

        candles.append({
            "timestamp": candle_ts,
            "open": float(quote["open"][i]),
            "high": float(quote["high"][i]),
            "low": float(quote["low"][i]),
            "close": float(quote["close"][i]),
            "volume": int(quote["volume"][i]) if quote["volume"][i] else 0
        })

    return candles


def _fetch_and_resample_candles(
    symbol: str,
    timeframe: TimeFrame,
    start_timestamp: Optional[int] = None
) -> List[Dict]:
    """
    Fetch 1h candles and resample to higher timeframes (2h, 3h, 4h, 5h).
    Yahoo Finance doesn't support these intervals directly.
    """
    resample_rule = RESAMPLE_TIMEFRAMES.get(timeframe)
    if not resample_rule:
        raise Exception(f"No resample rule for timeframe: {timeframe.value}")

    # Fetch 1h candles
    config = TIMEFRAME_MAP[TimeFrame.H1]

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    params = {
        "interval": config["interval"],
        "range": config["range"],
    }

    if start_timestamp:
        params.pop("range", None)
        params["period1"] = start_timestamp
        params["period2"] = int(datetime.now().timestamp())

    response = requests.get(url, headers=headers, params=params, timeout=30)

    if response.status_code != 200:
        raise Exception(f"Yahoo API returned status {response.status_code}")

    data = response.json()

    if "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
        error = data.get("chart", {}).get("error", {})
        raise Exception(f"Yahoo API error: {error.get('description', 'Unknown error')}")

    result = data["chart"]["result"][0]
    timestamps = result.get("timestamp", [])

    if not timestamps:
        return []

    # Validate quote data exists before accessing
    indicators = result.get("indicators", {})
    quotes = indicators.get("quote", [])
    if not quotes or len(quotes) == 0:
        return []
    
    quote = quotes[0]

    # Build DataFrame for resampling
    rows = []
    for i, ts in enumerate(timestamps):
        if any(quote[k][i] is None for k in ["open", "high", "low", "close"]):
            continue
        rows.append({
            "timestamp": datetime.utcfromtimestamp(ts).replace(microsecond=0),
            "open": float(quote["open"][i]),
            "high": float(quote["high"][i]),
            "low": float(quote["low"][i]),
            "close": float(quote["close"][i]),
            "volume": int(quote["volume"][i]) if quote["volume"][i] else 0
        })

    if not rows:
        return []

    df = pd.DataFrame(rows)
    df.set_index("timestamp", inplace=True)

    # Resample to target timeframe
    resampled = df.resample(resample_rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    # Convert back to list of dicts
    candles = []
    for ts, row in resampled.iterrows():
        candles.append({
            "timestamp": ts.to_pydatetime(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": int(row["volume"])
        })

    return candles


def get_existing_timestamps(db: Session, stock_id: int, timeframe: TimeFrame) -> set:
    """Get all existing timestamps for a stock/timeframe combination"""
    results = (
        db.query(Candle.timestamp)
        .filter(Candle.stock_id == stock_id, Candle.timeframe == timeframe)
        .all()
    )
    # For daily candles, use date only; for others, truncate to minute
    if timeframe == TimeFrame.D1:
        return {r[0].date() if r[0] else None for r in results}
    else:
        return {r[0].replace(second=0, microsecond=0) if r[0] else None for r in results}


def sync_candles(
    db: Session,
    symbol: str,
    timeframe: TimeFrame,
    full_sync: bool = False
) -> Dict:
    """
    Sync candles from Yahoo Finance API to database (incremental sync by default)
    Only fetches missing candles to minimize API calls and improve performance
    Returns: dict with sync stats
    """
    symbol = symbol.upper().strip()

    # Get or create stock
    stock = get_or_create_stock(db, symbol)

    # Determine start timestamp for sync
    start_timestamp = None
    latest_timestamp = None
    sync_type = "FULL"
    
    if not full_sync:
        latest_timestamp = get_latest_candle_timestamp(db, stock.id, timeframe)
        if latest_timestamp:
            # Start from latest + 1 second to avoid duplicates
            start_timestamp = int(latest_timestamp.timestamp()) + 1
            sync_type = "INCREMENTAL"
            print(f"🔄 {sync_type} sync: Fetching data after {latest_timestamp}")

            # Smart skip: For intraday timeframes, skip if latest candle is very recent
            # This avoids unnecessary API calls when we know there's no new data
            now = datetime.utcnow()
            time_diff = (now - latest_timestamp).total_seconds()

            # Define minimum time before checking for new candles
            min_check_intervals = {
                TimeFrame.M1: 60,      # 1 minute
                TimeFrame.M5: 300,     # 5 minutes
                TimeFrame.M15: 900,    # 15 minutes
                TimeFrame.M30: 1800,   # 30 minutes
                TimeFrame.H1: 3600,    # 1 hour
                TimeFrame.H2: 7200,    # 2 hours
                TimeFrame.H3: 10800,   # 3 hours
                TimeFrame.H4: 14400,   # 4 hours
                TimeFrame.H5: 18000,   # 5 hours
                TimeFrame.D1: 86400,   # 1 day
            }

            min_interval = min_check_intervals.get(timeframe, 60)

            # Skip API call if latest candle is too recent
            if timeframe != TimeFrame.M1 and time_diff < min_interval:
                print(f"⏭️  Skipping sync: Latest candle is only {int(time_diff)}s old (min: {min_interval}s)")
                return {
                    "success": True,
                    "symbol": symbol,
                    "timeframe": timeframe.value,
                    "new_candles": 0,
                    "sync_type": "SKIPPED",
                    "message": f"No new candles expected (last candle: {int(time_diff)}s ago, min interval: {min_interval}s)"
                }
    else:
        print(f"🔄 {sync_type} sync: Fetching all available history")

    # Fetch from API (Yahoo Finance or Binance for crypto)
    print(f"📡 Fetching from API: {symbol} {timeframe.value} (start: {start_timestamp or 'all history'})")
    try:
        candles_data = fetch_candles_from_yahoo_api(symbol, timeframe, start_timestamp)
    except Exception:
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "new_candles": 0
        }


    if not candles_data:
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "new_candles": 0,
            "message": "No new candles available"
        }

    # Get all existing timestamps for this stock/timeframe to check duplicates
    existing_timestamps = get_existing_timestamps(db, stock.id, timeframe)

    # Filter out candles that already exist
    new_candles = []
    for candle_data in candles_data:
        # For daily candles, compare by date only; for others, truncate to minute
        if timeframe == TimeFrame.D1:
            key = candle_data["timestamp"].date()
        else:
            key = candle_data["timestamp"].replace(second=0, microsecond=0)

        if key not in existing_timestamps:
            new_candles.append(candle_data)

    skipped_count = len(candles_data) - len(new_candles)

    if not new_candles:
        print(f"ℹ️  No new candles: {len(candles_data)} fetched, all already in DB")
        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe.value,
            "new_candles": 0,
            "skipped": skipped_count,
            "total_fetched": len(candles_data),
            "sync_type": sync_type,
            "message": "All candles already exist in database"
        }

    # Bulk insert only new candles
    candles_to_insert = [
        Candle(
            stock_id=stock.id,
            timeframe=timeframe,
            timestamp=candle_data["timestamp"],
            open=candle_data["open"],
            high=candle_data["high"],
            low=candle_data["low"],
            close=candle_data["close"],
            volume=candle_data["volume"]
        )
        for candle_data in new_candles
    ]

    db.bulk_save_objects(candles_to_insert)
    db.commit()

    # Log sync results
    print(f"✅ Sync complete: {len(new_candles)} new, {skipped_count} skipped, {len(candles_data)} total fetched")

    return {
        "success": True,
        "symbol": symbol,
        "timeframe": timeframe.value,
        "new_candles": len(new_candles),
        "skipped": skipped_count,
        "total_fetched": len(candles_data),
        "sync_type": sync_type,
        "latest_timestamp": candles_data[-1]["timestamp"].isoformat() if candles_data else None
    }


def sync_all_timeframes(db: Session, symbol: str, full_sync: bool = False) -> List[Dict]:
    """
    Sync all timeframes for a symbol in parallel for better performance.
    Uses ThreadPoolExecutor to fetch data from multiple timeframes concurrently.
    """
    from database import SessionLocal

    def sync_single_timeframe(tf: TimeFrame):
        """Helper function to sync a single timeframe with its own DB session"""
        # Create a new session for this thread
        thread_db = SessionLocal()
        try:
            result = sync_candles(thread_db, symbol, tf, full_sync)
            return result
        finally:
            thread_db.close()

    results = []

    # Use ThreadPoolExecutor for parallel syncing
    # Use 10 workers for maximum parallelism (APIs can handle it)
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all timeframe sync tasks
        future_to_tf = {executor.submit(sync_single_timeframe, tf): tf for tf in TimeFrame}

        # Collect results as they complete
        for future in as_completed(future_to_tf):
            tf = future_to_tf[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # If one timeframe fails, log it but continue with others
                print(f"Error syncing {tf.value}: {str(e)}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "symbol": symbol,
                    "timeframe": tf.value
                })

    # Sort results by timeframe order for consistent output
    timeframe_order = {tf.value: i for i, tf in enumerate(TimeFrame)}
    results.sort(key=lambda x: timeframe_order.get(x.get("timeframe", "1m"), 999))

    return results


def get_sync_status(db: Session, symbol: str) -> Dict:
    """Get sync status for all timeframes of a symbol"""
    stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()

    if not stock:
        return {"symbol": symbol, "exists": False, "timeframes": {}}

    status = {
        "symbol": symbol,
        "exists": True,
        "stock_name": stock.name,
        "timeframes": {}
    }

    for tf in TimeFrame:
        count = (
            db.query(Candle)
            .filter(Candle.stock_id == stock.id, Candle.timeframe == tf)
            .count()
        )
        latest = get_latest_candle_timestamp(db, stock.id, tf)

        status["timeframes"][tf.value] = {
            "candle_count": count,
            "latest_timestamp": latest.isoformat() if latest else None
        }

    return status


def remove_duplicate_candles(db: Session, symbol: str = None) -> Dict:
    """
    Remove duplicate candles from database.
    For daily candles, considers same date as duplicate (ignores time).
    For other timeframes, uses exact timestamp match.
    Keeps the candle with the lowest ID for each unique combination.
    """
    from sqlalchemy import func, and_, cast, Date

    total_removed = 0

    # Get stocks to process
    if symbol:
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        if not stock:
            return {"success": False, "error": f"Stock {symbol} not found"}
        stocks = [stock]
    else:
        stocks = db.query(Stock).all()

    for stock in stocks:
        for tf in TimeFrame:
            # Get all candles for this stock/timeframe
            candles = (
                db.query(Candle)
                .filter(Candle.stock_id == stock.id, Candle.timeframe == tf)
                .order_by(Candle.id)
                .all()
            )

            if not candles:
                continue

            # Track seen timestamps/dates and IDs to delete
            seen = set()
            ids_to_delete = []

            for candle in candles:
                # For daily candles, use date only; for others use full timestamp
                if tf == TimeFrame.D1:
                    key = candle.timestamp.date()
                else:
                    # Truncate to minute for intraday
                    key = candle.timestamp.replace(second=0, microsecond=0)

                if key in seen:
                    ids_to_delete.append(candle.id)
                else:
                    seen.add(key)

            if ids_to_delete:
                db.query(Candle).filter(Candle.id.in_(ids_to_delete)).delete(synchronize_session=False)
                total_removed += len(ids_to_delete)

    db.commit()

    return {
        "success": True,
        "duplicates_removed": total_removed,
        "message": f"Removed {total_removed} duplicate candles"
    }