#!/usr/bin/env python3
"""
Script to delete and re-sync all stocks with corrected UTC timestamps.
This fixes the timezone issue by removing old data and fetching fresh data.
Uses parallel processing to sync multiple stocks simultaneously.
"""

import requests
import sys
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

API_URL = "http://localhost:8000"

# Thread-safe printing
print_lock = threading.Lock()


def get_all_stocks() -> List[Dict]:
    """Fetch all stocks from the API"""
    try:
        response = requests.get(f"{API_URL}/stocks")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching stocks: {e}")
        return []


def delete_stock(symbol: str) -> Dict:
    """Delete a stock and all its data"""
    try:
        response = requests.delete(f"{API_URL}/stocks/{symbol}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  ├─ ⚠️  Error deleting {symbol}: {e}")
        return {}


def sync_stock(symbol: str) -> Dict:
    """Sync all timeframes for a stock"""
    try:
        response = requests.post(f"{API_URL}/candles/{symbol}/sync")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        with print_lock:
            print(f"  └─ ⚠️  Error syncing {symbol}: {e}")
        return {}


def process_single_stock(symbol: str, idx: int, total: int) -> Dict:
    """Process a single stock: delete old data and re-sync"""
    with print_lock:
        print(f"[{idx}/{total}] Processing {symbol}...")
        print("  ├─ Deleting old data...")
    
    delete_result = delete_stock(symbol)
    deleted_candles = delete_result.get('deleted', {}).get('candles', 0)
    
    with print_lock:
        if deleted_candles > 0:
            print(f"  ├─ ✅ Deleted {deleted_candles} candles")
        else:
            print("  ├─ ⚠️  Stock not found or already deleted")
        print("  ├─ Re-syncing with correct timestamps...")
    
    sync_result = sync_stock(symbol)
    
    # Calculate total new candles
    results = sync_result.get('results', [])
    new_candles = sum(r.get('new_candles', 0) for r in results)
    
    with print_lock:
        if new_candles > 0:
            print(f"  └─ ✅ Synced {new_candles} new candles")
        else:
            print("  └─ ⚠️  Sync completed but no candles added")
        print()
    Using PARALLEL processing for faster execution...")
    print("=" * 50)
    print()
    
    # Process stocks in parallel (max 5 stocks at a time to avoid overwhelming API)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all stock processing tasks
        future_to_symbol = {
            executor.submit(process_single_stock, symbol, idx, total): symbol 
            for idx, symbol in enumerate(symbols, 1)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                symbol = future_to_symbol[future]
                with print_lock:
                    print(f"❌ Error processing {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'success': False,
                    'error': str(e)
                }cks:
        print("❌ No stocks found or API is not responding")
        sys.exit(1)
    
    symbols = [s['symbol'] for s in stocks]
    print(f"Found stocks: {', '.join(symbols)}")
    print()
    
    total = len(symbols)
    print("=" * 50)
    print("Starting deletion and re-sync process...")
    print("=" * 50)
    print()
    
    for idx, symbol in enumerate(symbols, 1):
        print(f"[{idx}/{total}] Processing {symbol}...")
        print("  ├─ Deleting old data...")
        
        delete_result = delete_stock(symbol)
        deleted_candles = delete_result.get('deleted', {}).get('candles', 0)
        
        if deleted_candles > 0:
            print(f"  ├─ ✅ Deleted {deleted_candles} candles")
        else:
            print("  ├─ ⚠️  Stock not found or already deleted")
        
        print("  ├─ Re-syncing with correct timestamps...")
        sync_result = sync_stock(symbol)
        
        # Calculate total new candles
        results = sync_result.get('results', [])
        new_candles = sum(r.get('new_candles', 0) for r in results)
        
        if new_candles > 0:
            print(f"  └─ ✅ Synced {new_candles} new candles")
        else:
            print("  └─ ⚠️  Sync completed but no candles added")
        
        print()
    
    print("=" * 50)
    print("✅ Re-sync Complete!")
    print("=" * 50)
    print()
    print("Summary:")
    print(f"  • Total stocks processed: {total}")
    print("  • All stocks now have UTC timestamps (OPEN time)")
    successful = sum(1 for r in results if r.get('success'))
    print(f"  • Successfully synced: {successful}/{total}")
    total_candles = sum(r.get('new_candles', 0) for r in results)
    print(f"  • Total candles synced: {total_candles}")
    print("  • Frontend will display in IST automatically")
    print()
    print("Next steps:")
    print("  1. Refresh your browser")
    print("  2. Check the charts - timestamps should match current IST time")
    print("  3. Verify latest candles are up-to-date")
    print()


if __name__ == "__main__":
    main()

