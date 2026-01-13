#!/usr/bin/env python3
"""Simple market structure test with clear pivots"""

import pandas as pd
from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy

print("=" * 70)
print("SIMPLE MARKET STRUCTURE TEST")
print("=" * 70)

# Create simple pattern: low, HIGH, low, low, LOW, high, low
# This should create clear swing pivots
prices = []

# Start low
for i in range(60):
    prices.append(100 - i * 0.5)  # Downtrend to 70

# Make a HIGH
for i in range(60):
    prices.append(70 + i * 1.0)  # Uptrend to 130

# Go down
for i in range(60):
    prices.append(130 - i * 0.7)  # Downtrend to 88

# Make another HIGH (higher than first)
for i in range(60):
    prices.append(88 + i * 1.2)  # Uptrend to 160

# Go down again
for i in range(60):
    prices.append(160 - i * 0.5)  # Downtrend to 130

# Extra bars for pivot detection
for i in range(60):
    prices.append(130 + i * 0.1)

df = pd.DataFrame({
    'open': prices,
    'high': [p * 1.005 for p in prices],
    'low': [p * 0.995 for p in prices],
    'close': prices,
    'volume': [1000] * len(prices)
})

print(f"\nTotal bars: {len(df)}")
print(f"Price range: {min(prices):.1f} - {max(prices):.1f}")

strategy = MTFLuxAlgo5thStrategy()

# Process incrementally to detect pivots
print("\nProcessing data incrementally...")
print("-" * 70)

detected_structures = []
for i in range(120, len(df), 10):
    df_subset = df.iloc[:i]
    result = strategy.calculate(df_subset)
    
    ms = result['indicators']['market_structure']
    seq = result['indicators']['pattern_sequence']
    sH = result['indicators']['pivot_swing_high']
    sL = result['indicators']['pivot_swing_low']
    
    if ms != "None" and ms not in detected_structures:
        detected_structures.append(ms)
        print(f"Bar {i:3d}: {ms:3s} | Seq: {seq:20s} | sH: {sH if sH else 'None':>6} | sL: {sL if sL else 'None':>6}")

# Final result
print("\n" + "=" * 70)
print("FINAL STATE")
print("=" * 70)
result = strategy.calculate(df)

print(f"Signal:           {result['signal']}")
print(f"Reason:           {result['reason']}")
print(f"Market Structure: {result['indicators']['market_structure']}")
print(f"Trend:            {result['indicators']['trend']}")
print(f"Sequence:         {result['indicators']['pattern_sequence']}")
print(f"Last Swing High:  {result['indicators']['last_swing_high']}")
print(f"Last Swing Low:   {result['indicators']['last_swing_low']}")

print("\n" + "=" * 70)
print("✓ Test complete!")
print("=" * 70)

