"""
Binance API service for fetching cryptocurrency candle data.
Provides proper OHLC data for all timeframes including 1m.
"""
import requests
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from models import TimeFrame


# Binance interval mapping
BINANCE_INTERVALS = {
    TimeFrame.M1: "1m",
    TimeFrame.M5: "5m",
    TimeFrame.M15: "15m",
    TimeFrame.M30: "30m",
    TimeFrame.H1: "1h",
    TimeFrame.H2: "2h",
    TimeFrame.H3: "3h",  # Note: Binance doesn't have 3h, we'll use 1h and resample
    TimeFrame.H4: "4h",
    TimeFrame.H5: "5h",  # Note: Binance doesn't have 5h, we'll use 1h and resample
    TimeFrame.D1: "1d",
}

# Binance supports: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
# We need to resample for 3h and 5h
BINANCE_RESAMPLE_TIMEFRAMES = {
    TimeFrame.H3: "3h",
    TimeFrame.H5: "5h",
}

# Known crypto symbols that should use Binance
# Format: Yahoo symbol -> Binance symbol
# Note: You can also use Binance symbols directly (e.g., BTCUSDT, SOLUSDT, ETHUSDT)
CRYPTO_SYMBOL_MAP = {
    "SOL-USD": "SOLUSDT",
    "BTC-USD": "BTCUSDT",
    "ETH-USD": "ETHUSDT",
    "XRP-USD": "XRPUSDT",
    "ADA-USD": "ADAUSDT",
    "DOGE-USD": "DOGEUSDT",
    "DOT-USD": "DOTUSDT",
    "MATIC-USD": "MATICUSDT",
    "LINK-USD": "LINKUSDT",
    "AVAX-USD": "AVAXUSDT",
    "SHIB-USD": "SHIBUSDT",
    "LTC-USD": "LTCUSDT",
    "UNI-USD": "UNIUSDT",
    "ATOM-USD": "ATOMUSDT",
    "XLM-USD": "XLMUSDT",
    "ALGO-USD": "ALGOUSDT",
    "VET-USD": "VETUSDT",
    "FIL-USD": "FILUSDT",
    "TRX-USD": "TRXUSDT",
    "ETC-USD": "ETCUSDT",
    "NEAR-USD": "NEARUSDT",
    "FTM-USD": "FTMUSDT",
    "SAND-USD": "SANDUSDT",
    "MANA-USD": "MANAUSDT",
    "AXS-USD": "AXSUSDT",
    "AAVE-USD": "AAVEUSDT",
    "GRT-USD": "GRTUSDT",
    "THETA-USD": "THETAUSDT",
    "XTZ-USD": "XTZUSDT",
    "EOS-USD": "EOSUSDT",
    "BNB-USD": "BNBUSDT",
    "ARB-USD": "ARBUSDT",
    "OP-USD": "OPUSDT",
    "PEPE-USD": "PEPEUSDT",
    "INJ-USD": "INJUSDT",
    "SUI-USD": "SUIUSDT",
    "APT-USD": "APTUSDT",
}

# Base URL for Binance API
BINANCE_API_URL = "https://api.binance.com/api/v3"


def is_crypto_symbol(symbol: str) -> bool:
    """Check if a symbol is a cryptocurrency (should use Binance)"""
    symbol = symbol.upper().strip()
    # Check if it's in our known crypto map
    if symbol in CRYPTO_SYMBOL_MAP:
        return True
    # Check if it ends with -USD (common crypto format on Yahoo)
    if symbol.endswith("-USD") and not symbol.startswith("^"):
        # Additional check: crypto symbols typically don't have dots
        base = symbol.replace("-USD", "")
        if "." not in base and len(base) <= 6:
            return True
    # Check if it's a direct Binance format (ends with USDT, USDC, BUSD, etc.)
    if symbol.endswith("USDT") or symbol.endswith("USDC") or symbol.endswith("BUSD"):
        return True
    # Check if it's in the values of CRYPTO_SYMBOL_MAP (reverse lookup)
    if symbol in CRYPTO_SYMBOL_MAP.values():
        return True
    return False


def get_binance_symbol(yahoo_symbol: str) -> str:
    """Convert Yahoo Finance symbol to Binance symbol"""
    yahoo_symbol = yahoo_symbol.upper().strip()
    if yahoo_symbol in CRYPTO_SYMBOL_MAP:
        return CRYPTO_SYMBOL_MAP[yahoo_symbol]
    # If it's already in Binance format (ends with USDT, USDC, BUSD), return as-is
    if yahoo_symbol.endswith("USDT") or yahoo_symbol.endswith("USDC") or yahoo_symbol.endswith("BUSD"):
        return yahoo_symbol
    # Try to convert -USD to USDT format
    if yahoo_symbol.endswith("-USD"):
        base = yahoo_symbol.replace("-USD", "")
        return f"{base}USDT"
    return yahoo_symbol


def fetch_binance_candles(
    symbol: str,
    timeframe: TimeFrame,
    start_timestamp: Optional[int] = None,
    limit: int = 1000
) -> List[Dict]:
    """
    Fetch candles from Binance API.

    Args:
        symbol: Yahoo Finance format symbol (e.g., "SOL-USD")
        timeframe: TimeFrame enum
        start_timestamp: Unix timestamp to start from (seconds)
        limit: Max candles to fetch (Binance max is 1000)

    Returns:
        List of candle dictionaries with timestamp, open, high, low, close, volume
    """
    binance_symbol = get_binance_symbol(symbol)

    # Check if this timeframe needs resampling
    if timeframe in BINANCE_RESAMPLE_TIMEFRAMES:
        return _fetch_and_resample_binance_candles(symbol, timeframe, start_timestamp)

    interval = BINANCE_INTERVALS.get(timeframe)
    if not interval:
        raise Exception(f"Unsupported timeframe for Binance: {timeframe.value}")

    # Limit data range for 1m timeframe to prevent excessive API calls
    # BUT respect incremental sync - if we have existing data, only fetch new data
    is_incremental = start_timestamp is not None
    
    if not start_timestamp:
        if timeframe == TimeFrame.M1:
            # 1m: Last 7 days only for FULL sync
            start_timestamp = int((datetime.utcnow() - timedelta(days=7)).timestamp())
            print(f"⚠️  FULL sync: Limiting 1m data to last 7 days for {binance_symbol}")
        elif timeframe == TimeFrame.M5:
            # 5m: Last 30 days for FULL sync
            start_timestamp = int((datetime.utcnow() - timedelta(days=30)).timestamp())
            print(f"⚠️  FULL sync: Limiting 5m data to last 30 days for {binance_symbol}")
        elif timeframe in [TimeFrame.M15, TimeFrame.M30]:
            # 15m, 30m: Last 60 days for FULL sync
            start_timestamp = int((datetime.utcnow() - timedelta(days=60)).timestamp())
            print(f"⚠️  FULL sync: Limiting {timeframe.value} data to last 60 days for {binance_symbol}")
    else:
        # Incremental sync - fetch from start_timestamp onwards
        print(f"🔄 INCREMENTAL sync: Fetching {binance_symbol} {timeframe.value} from timestamp {start_timestamp}")

    url = f"{BINANCE_API_URL}/klines"

    params = {
        "symbol": binance_symbol,
        "interval": interval,
    }

    # For incremental sync, use reasonable limit without endTime
    # endTime can cause unexpected behavior when combined with startTime + limit
    if is_incremental:
        # Use Binance max limit for efficiency
        params["limit"] = 1000
    else:
        # Full sync: use default limit
        params["limit"] = limit

    if start_timestamp:
        # Binance uses milliseconds
        params["startTime"] = start_timestamp * 1000

    # Add API key if available (for higher rate limits)
    headers = {}
    api_key = os.environ.get("BINANCE_API_KEY")
    if api_key:
        headers["X-MBX-APIKEY"] = api_key

    all_candles = []
    # For incremental sync with endTime set, usually only need 1-2 requests
    max_requests = 3 if is_incremental else 20
    request_count = 0

    # Binance returns max 1000 candles per request, so we may need multiple requests
    while request_count < max_requests:
        request_count += 1
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠️  Binance API timeout on request {request_count}, returning partial data")
            break
        except Exception as e:
            print(f"❌ Binance API error on request {request_count}: {str(e)}")
            break

        if response.status_code != 200:
            error_msg = response.json().get("msg", response.text) if response.text else f"Status {response.status_code}"
            print(f"❌ Binance API error (request {request_count}): {error_msg}")
            break

        data = response.json()

        if not data:
            break

        # Progress logging
        if request_count == 1 or request_count % 5 == 0:
            print(f"📊 Fetched {len(all_candles) + len(data)} candles for {binance_symbol} {timeframe.value} (request {request_count})")

        for kline in data:
            # Binance kline format:
            # [0] Open time, [1] Open, [2] High, [3] Low, [4] Close, [5] Volume,
            # [6] Close time, [7] Quote asset volume, [8] Number of trades,
            # [9] Taker buy base volume, [10] Taker buy quote volume, [11] Ignore

            # Use OPEN time for candle timestamp (when the candle starts)
            # This is better for real-time trading as data is available immediately
            open_time_ms = kline[0]
            candle_ts = datetime.utcfromtimestamp(open_time_ms / 1000).replace(microsecond=0)

            all_candles.append({
                "timestamp": candle_ts,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": int(float(kline[5]))  # Base asset volume
            })

        # If we got less than limit, we've fetched all available data
        if len(data) < limit:
            break

        # Update startTime for next request (last candle's close time + 1)
        if not data or len(data) == 0 or len(data[-1]) < 7:
            break
        last_close_time = data[-1][6]
        params["startTime"] = last_close_time + 1
    
    # Warn if we hit the max request limit
    if request_count >= max_requests:
        print(f"⚠️  Hit max request limit ({max_requests}) for {binance_symbol} {timeframe.value}. Returning {len(all_candles)} candles.")

    print(f"✅ Completed: {len(all_candles)} total candles for {binance_symbol} {timeframe.value}")
    return all_candles


def _fetch_and_resample_binance_candles(
    symbol: str,
    timeframe: TimeFrame,
    start_timestamp: Optional[int] = None
) -> List[Dict]:
    """
    Fetch 1h candles from Binance and resample to 3h or 5h.
    Binance doesn't support 3h and 5h intervals directly.
    """
    import pandas as pd

    resample_rule = BINANCE_RESAMPLE_TIMEFRAMES.get(timeframe)
    if not resample_rule:
        raise Exception(f"No resample rule for timeframe: {timeframe.value}")

    # Fetch 1h candles
    binance_symbol = get_binance_symbol(symbol)
    url = f"{BINANCE_API_URL}/klines"

    params = {
        "symbol": binance_symbol,
        "interval": "1h",
        "limit": 1000,
    }

    if start_timestamp:
        params["startTime"] = start_timestamp * 1000

    headers = {}
    api_key = os.environ.get("BINANCE_API_KEY")
    if api_key:
        headers["X-MBX-APIKEY"] = api_key

    all_candles = []
    max_requests = 20  # Prevent infinite loops
    request_count = 0

    while request_count < max_requests:
        request_count += 1
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠️  Binance API timeout on resample request {request_count}, returning partial data")
            break
        except Exception as e:
            print(f"❌ Binance API error on resample request {request_count}: {str(e)}")
            break

        if response.status_code != 200:
            error_msg = response.json().get("msg", response.text) if response.text else f"Status {response.status_code}"
            print(f"❌ Binance API error (resample request {request_count}): {error_msg}")
            break

        data = response.json()

        if not data:
            break

        for kline in data:
            # Use OPEN time for candle timestamp (when the candle starts)
            open_time_ms = kline[0]
            candle_ts = datetime.utcfromtimestamp(open_time_ms / 1000).replace(microsecond=0)

            all_candles.append({
                "timestamp": candle_ts,
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": int(float(kline[5]))
            })

        if len(data) < 1000:
            break

        if not data or len(data) == 0 or len(data[-1]) < 7:
            break
        last_close_time = data[-1][6]
        params["startTime"] = last_close_time + 1
    
    if request_count >= max_requests:
        print(f"⚠️  Hit max request limit ({max_requests}) for resample operation")

    if not all_candles:
        return []

    # Create DataFrame and resample
    df = pd.DataFrame(all_candles)
    df.set_index("timestamp", inplace=True)

    resampled = df.resample(resample_rule).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum"
    }).dropna()

    # Convert back to list of dicts
    result = []
    for ts, row in resampled.iterrows():
        result.append({
            "timestamp": ts.to_pydatetime(),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": int(row["volume"])
        })

    return result


def get_binance_historical_candles(
    symbol: str,
    timeframe: TimeFrame,
    start_timestamp: Optional[int] = None
) -> List[Dict]:
    """
    Fetch all available historical candles from Binance.
    This handles pagination automatically.

    Args:
        symbol: Yahoo Finance format symbol (e.g., "SOL-USD")
        timeframe: TimeFrame enum
        start_timestamp: Unix timestamp to start from (seconds)

    Returns:
        List of all candle dictionaries
    """
    return fetch_binance_candles(symbol, timeframe, start_timestamp, limit=1000)
