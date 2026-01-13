#!/usr/bin/env python3
"""Test plotting data availability"""

from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy
import pandas as pd
import numpy as np

# Create test data
prices = []
for i in range(200):
    prices.append(100 + 20 * np.sin(i / 10))

df = pd.DataFrame({
    'open': prices,
    'high': [p * 1.01 for p in prices],
    'low': [p * 0.99 for p in prices],
    'close': prices,
    'volume': [1000] * len(prices),
    'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1h')
})

strategy = MTFLuxAlgo5thStrategy()
result = strategy.calculate(df)

print("=" * 70)
print("MTF LUXALGO 5TH - PLOTTING DATA TEST")
print("=" * 70)
print(f"\nSignal: {result['signal']}")
print(f"Reason: {result['reason']}")
print(f"\nPlottable indicators:")

for key in result['indicators'].keys():
    if '_line' in key or key == 'timestamps':
        value = result['indicators'][key]
        if isinstance(value, list):
            print(f"  {key:25s}: {len(value)} points")

print(f"\nSample volatility_line (first 5): {result['indicators']['volatility_line'][:5]}")
print(f"Sample internal_length_line (first 5): {result['indicators']['internal_length_line'][:5]}")
print(f"Sample timestamps (first 3): {result['indicators']['timestamps'][:3]}")

print("\n" + "=" * 70)
print("✓ Plotting data available!")
print("=" * 70)

