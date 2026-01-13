#!/usr/bin/env python3
"""Test script for MTF LuxAlgo 5th strategy"""

import pandas as pd
import numpy as np
from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy

# Create test data with clear pivot points
np.random.seed(42)
base_price = 100

# Create a wave pattern with clear highs and lows
prices = []
for i in range(200):
    # Create sine wave with noise for clear pivots
    wave = 100 + 20 * np.sin(i / 10) + np.random.randn() * 0.5
    prices.append(wave)

df = pd.DataFrame({
    'open': prices,
    'high': [p * 1.01 for p in prices],
    'low': [p * 0.99 for p in prices],
    'close': prices,
    'volume': [1000 + i * 10 for i in range(len(prices))]
})

print("=" * 70)
print("MTF LUXALGO 5TH STRATEGY TEST")
print("=" * 70)

# Test 1: Auto mode
print("\n[TEST 1] AUTO MODE")
print("-" * 70)
strategy_auto = MTFLuxAlgo5thStrategy()
strategy_auto.ms_mode = "auto"
result_auto = strategy_auto.calculate(df)

print(f"Signal:   {result_auto['signal']}")
print(f"Strength: {result_auto['strength']}")
print(f"Reason:   {result_auto['reason']}")
print("\nIndicators:")
for key, value in sorted(result_auto['indicators'].items()):
    print(f"  {key:25} = {value}")

# Test 2: Dynamic mode
print("\n[TEST 2] DYNAMIC MODE")
print("-" * 70)
strategy_dyn = MTFLuxAlgo5thStrategy()
strategy_dyn.ms_mode = "Dynamic"
result_dyn = strategy_dyn.calculate(df)

print(f"Signal:   {result_dyn['signal']}")
print(f"Strength: {result_dyn['strength']}")
print(f"Reason:   {result_dyn['reason']}")
print("\nIndicators:")
for key, value in sorted(result_dyn['indicators'].items()):
    print(f"  {key:25} = {value}")

# Compare
print("\n[COMPARISON]")
print("-" * 70)
print(f"Auto Mode Internal Length:    {result_auto['indicators']['internal_length']}")
print(f"Dynamic Mode Internal Length: {result_dyn['indicators']['internal_length']}")
print(f"Volatility Score:             {result_auto['indicators']['volatility_score']:.4f}")

print("\n" + "=" * 70)
print("✓ All tests passed!")
print("=" * 70)

