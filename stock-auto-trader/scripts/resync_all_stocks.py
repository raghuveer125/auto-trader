#!/usr/bin/env python3
"""
Script to delete and re-sync all stocks with corrected UTC timestamps.
This fixes the timezone issue by removing old data and fetching fresh data.
"""

import requests
import sys
from typing import List, Dict

API_URL = "http://localhost:8000"


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
        print(f"  └─ ⚠️  Error syncing {symbol}: {e}")
        return {}


def main():
    print("=" * 50)
    print("Stock Re-sync Script")
    print("=" * 50)
    print()
    print("⚠️  WARNING: This will delete ALL candles and indicators for ALL stocks!")
    print("   (Trades and portfolio will NOT be affected)")
    print()
    
    confirm = input("Do you want to continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Aborted by user")
        sys.exit(0)
    
    print()
    print("📊 Fetching list of all stocks...")
    stocks = get_all_stocks()
    
    if not stocks:
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
    print("  • Frontend will display in IST automatically")
    print()
    print("Next steps:")
    print("  1. Refresh your browser")
    print("  2. Check the charts - timestamps should match current IST time")
    print("  3. Verify latest candles are up-to-date")
    print()


if __name__ == "__main__":
    main()

