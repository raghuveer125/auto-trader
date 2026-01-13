#!/usr/bin/env python3
"""Test pivot detection functions"""

import pandas as pd
import numpy as np
from strategies.mtf_luxalgo_5th import f_pivothigh, f_pivotlow

# Create simple test data with known pivots
# Pattern: low, HIGH, low, low, LOW, high
prices_high = [10, 15, 12, 11, 9, 13, 11]  # Pivot high at index 1 (value 15)
prices_low = [10, 8, 12, 11, 9, 13, 11]    # Pivot low at index 1 (value 8)

print("=" * 70)
print("PIVOT DETECTION TEST")
print("=" * 70)

# Test 1: Pivot High Detection
print("\n[TEST 1] PIVOT HIGH DETECTION")
print("-" * 70)
print(f"Data: {prices_high}")
series_high = pd.Series(prices_high)

# Test with left=2, right=2 (should find pivot at index 1, value 15)
# But we're checking from current position, so we need more data
for left in [1, 2]:
    for right in [1, 2]:
        result = f_pivothigh(series_high, left, right)
        print(f"  left={left}, right={right}: {result}")

# Test 2: Pivot Low Detection
print("\n[TEST 2] PIVOT LOW DETECTION")
print("-" * 70)
print(f"Data: {prices_low}")
series_low = pd.Series(prices_low)

for left in [1, 2]:
    for right in [1, 2]:
        result = f_pivotlow(series_low, left, right)
        print(f"  left={left}, right={right}: {result}")

# Test 3: Realistic wave pattern
print("\n[TEST 3] WAVE PATTERN")
print("-" * 70)
wave = []
for i in range(100):
    wave.append(100 + 20 * np.sin(i / 5))

df_wave = pd.DataFrame({
    'high': wave,
    'low': wave
})

# Check last 20 bars for pivots
print("Checking for pivots with left=5, right=5:")
for i in range(80, 100):
    df_subset = df_wave.iloc[:i+1]
    ph = f_pivothigh(df_subset['high'], 5, 5)
    pl = f_pivotlow(df_subset['low'], 5, 5)
    if ph is not None or pl is not None:
        ph_str = f"{ph:.2f}" if ph is not None else "None"
        pl_str = f"{pl:.2f}" if pl is not None else "None"
        print(f"  Bar {i}: PH={ph_str:>6}, PL={pl_str:>6}")

print("\n" + "=" * 70)
print("✓ Pivot detection tests complete!")
print("=" * 70)

