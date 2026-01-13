#!/usr/bin/env python3
"""Debug pivot detection"""

import pandas as pd
from strategies.mtf_luxalgo_5th import f_pivothigh, f_pivotlow

# Create sine wave pattern with clear peaks and troughs
import numpy as np
prices = []
for i in range(200):
    prices.append(100 + 20 * np.sin(i / 10))  # Smooth sine wave

df = pd.DataFrame({
    'high': prices,
    'low': prices
})

print("=" * 70)
print("PIVOT DETECTION DEBUG")
print("=" * 70)
print(f"Total bars: {len(df)}")
print(f"Testing with swing_length = 50")
print("-" * 70)

# Test at different positions
for i in range(120, 200, 10):
    df_subset = df.iloc[:i]
    
    # Try to find pivots with swing_length = 50
    ph = f_pivothigh(df_subset['high'], 50, 50)
    pl = f_pivotlow(df_subset['low'], 50, 50)
    
    if ph is not None or pl is not None:
        print(f"Bar {i}: PH={ph if ph else 'None':>6}, PL={pl if pl else 'None':>6}")

print("\n" + "=" * 70)
print("Testing with smaller length = 5")
print("-" * 70)

# Test with smaller length
for i in range(20, 200, 10):
    df_subset = df.iloc[:i]
    
    # Try to find pivots with length = 5
    ph = f_pivothigh(df_subset['high'], 5, 5)
    pl = f_pivotlow(df_subset['low'], 5, 5)
    
    if ph is not None or pl is not None:
        print(f"Bar {i}: PH={ph if ph else 'None':>6}, PL={pl if pl else 'None':>6}")

print("\n" + "=" * 70)
print("✓ Debug complete!")
print("=" * 70)

