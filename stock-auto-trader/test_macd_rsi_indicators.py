#!/usr/bin/env python3
"""
Test script to verify MACD and RSI indicators are being returned correctly
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Test indicators endpoint for MACD
print("Testing /indicators endpoint for MACD...")
response = requests.get(
    f"{BASE_URL}/indicators/INFY",
    params={"timeframe": "1d", "strategy": "MACD", "limit": 50}
)

if response.status_code == 200:
    data = response.json()
    print("\n✓ MACD Indicators Response:")
    print(f"  - Candles: {data.get('candle_count')}")
    print(f"  - Strategies: {data.get('strategies')}")
    
    if 'MACD' in data.get('indicators', {}):
        macd_data = data['indicators']['MACD']
        print(f"\n  MACD Data Keys: {list(macd_data.keys())}")
        print(f"  - Signal points: {len(macd_data.get('signal', []))}")
        print(f"  - Timestamps: {len(macd_data.get('timestamps', []))}")
        print(f"  - MACD line: {len(macd_data.get('macd_line', []))}")
        print(f"  - Signal line: {len(macd_data.get('macd_signal', []))}")
        print(f"  - Histogram: {len(macd_data.get('macd_histogram', []))}")
        
        # Show sample data
        if macd_data.get('macd_line'):
            print(f"\n  Sample MACD line (first 3): {macd_data['macd_line'][:3]}")
            print(f"  Sample Signal line (first 3): {macd_data.get('macd_signal', [])[:3]}")
            print(f"  Sample Histogram (first 3): {macd_data.get('macd_histogram', [])[:3]}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)

# Test RSI
print("\n" + "="*60)
print("Testing /indicators endpoint for RSI...")
response = requests.get(
    f"{BASE_URL}/indicators/INFY",
    params={"timeframe": "1d", "strategy": "RSI", "limit": 50}
)

if response.status_code == 200:
    data = response.json()
    print("\n✓ RSI Indicators Response:")
    print(f"  - Candles: {data.get('candle_count')}")
    print(f"  - Strategies: {data.get('strategies')}")
    
    if 'RSI' in data.get('indicators', {}):
        rsi_data = data['indicators']['RSI']
        print(f"\n  RSI Data Keys: {list(rsi_data.keys())}")
        print(f"  - Signal points: {len(rsi_data.get('signal', []))}")
        print(f"  - Timestamps: {len(rsi_data.get('timestamps', []))}")
        print(f"  - RSI values: {len(rsi_data.get('rsi_value', []))}")
        
        # Show sample data
        if rsi_data.get('rsi_value'):
            print(f"\n  Sample RSI values (first 3): {rsi_data['rsi_value'][:3]}")
            print(f"  Sample Timestamps (first 3): {rsi_data.get('timestamps', [])[:3]}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)
