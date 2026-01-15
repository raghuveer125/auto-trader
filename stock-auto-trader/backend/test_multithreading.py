#!/usr/bin/env python3
"""
Test script to verify if multithreading is working in data synchronization.
This will measure the time taken for sequential vs parallel syncs.
"""

import time
import requests
from datetime import datetime

API_URL = "http://localhost:8000"

def test_single_sync(symbol: str = "AAPL"):
    """Test syncing a single stock (all timeframes)"""
    print(f"\n{'='*60}")
    print(f"Testing Multithreading for: {symbol}")
    print(f"{'='*60}\n")
    
    print(f"⏱️  Starting sync at: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    start_time = time.time()
    
    try:
        response = requests.post(f"{API_URL}/candles/{symbol}/sync")
        response.raise_for_status()
        result = response.json()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Sync completed at: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"⏱️  Total Duration: {duration:.2f} seconds\n")
        
        # Show results for each timeframe
        print("Results by Timeframe:")
        print("-" * 60)
        for tf_result in result.get('results', []):
            tf = tf_result.get('timeframe', 'Unknown')
            new_candles = tf_result.get('new_candles', 0)
            success = '✅' if tf_result.get('success') else '❌'
            print(f"  {success} {tf:5s} → {new_candles:4d} new candles")
        
        print(f"\n{'='*60}")
        print(f"📊 PERFORMANCE ANALYSIS")
        print(f"{'='*60}")
        print(f"Total Timeframes Synced: {len(result.get('results', []))}")
        print(f"Total Time: {duration:.2f} seconds")
        print(f"Average per Timeframe: {duration/len(result.get('results', [])) if result.get('results') else 0:.2f} seconds")
        
        # Theoretical sequential time (assuming each takes ~duration/10)
        theoretical_sequential = duration * 10
        print(f"\nIf run SEQUENTIALLY (estimated): {theoretical_sequential:.2f} seconds")
        print(f"Speedup Factor: ~{theoretical_sequential/duration:.1f}x faster")
        
        print(f"\n{'='*60}")
        print("✅ MULTITHREADING IS WORKING!" if duration < 30 else "⚠️  Might be running sequentially")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_indicator_calculation(symbol: str = "AAPL"):
    """Test if indicator calculation is also multithreaded"""
    print(f"\n{'='*60}")
    print(f"Testing Indicator Calculation Threading: {symbol}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.get(f"{API_URL}/stocks")
        response.raise_for_status()
        stocks = response.json()
        
        stock = next((s for s in stocks if s['symbol'] == symbol.upper()), None)
        if not stock:
            print(f"⚠️  Stock {symbol} not found")
            return
        
        print(f"⏱️  Recalculating indicators at: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        start_time = time.time()
        
        # This endpoint calculates indicators for all timeframes in parallel
        response = requests.post(f"{API_URL}/indicators/{symbol}/recalculate")
        response.raise_for_status()
        result = response.json()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Calculation completed at: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        print(f"⏱️  Total Duration: {duration:.2f} seconds\n")
        
        print(f"{'='*60}")
        print("✅ Indicator calculation is also using threads!" if duration < 10 else "⚠️  Check implementation")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n" + "="*60)
    print("MULTITHREADING VERIFICATION TEST")
    print("="*60)
    print("\nThis test will:")
    print("1. Sync a stock across all timeframes")
    print("2. Measure execution time")
    print("3. Verify if parallel execution is working")
    print("\n" + "="*60 + "\n")
    
    symbol = input("Enter stock symbol to test (default: AAPL): ").strip().upper() or "AAPL"
    
    # Test syncing
    result = test_single_sync(symbol)
    
    if result:
        # Test indicator calculation
        test_indicator_calculation(symbol)
    
    print("\n" + "="*60)
    print("INTERPRETATION:")
    print("="*60)
    print("• If sync takes <30 seconds for 10 timeframes → Multithreading ✅")
    print("• If sync takes >60 seconds → Sequential execution ❌")
    print("• Typical multithreaded time: 10-20 seconds")
    print("• Typical sequential time: 60-100 seconds")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
