#!/usr/bin/env python3
"""Test market structure detection"""

import pandas as pd
import numpy as np
from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy

print("=" * 70)
print("MARKET STRUCTURE DETECTION TEST")
print("=" * 70)

# Create uptrend data: Higher Highs and Higher Lows
print("\n[TEST 1] UPTREND - Higher Highs & Higher Lows")
print("-" * 70)

uptrend_prices = []
for i in range(300):
    # Upward trend with oscillations
    base = 100 + i * 0.2
    wave = 10 * np.sin(i / 15)
    uptrend_prices.append(base + wave)

df_up = pd.DataFrame({
    'open': uptrend_prices,
    'high': [p * 1.01 for p in uptrend_prices],
    'low': [p * 0.99 for p in uptrend_prices],
    'close': uptrend_prices,
    'volume': [1000] * len(uptrend_prices)
})

strategy = MTFLuxAlgo5thStrategy()

# Simulate historical analysis by processing data incrementally
# This allows pivots to be detected (they need future bars)
for i in range(150, len(df_up), 20):
    df_subset = df_up.iloc[:i]
    result = strategy.calculate(df_subset)

    # Print when we detect structure
    if result['indicators']['market_structure'] != "None":
        print(f"Bar {i}: {result['indicators']['market_structure']} detected")
        print(f"  Sequence: {result['indicators']['pattern_sequence']}")

# Final result
result = strategy.calculate(df_up.iloc[:250])  # Use 250 bars so last 50 can be pivots

print(f"\nFinal Signal:   {result['signal']}")
print(f"Strength:       {result['strength']}")
print(f"Reason:         {result['reason']}")
print(f"\nMarket Structure: {result['indicators']['market_structure']}")
print(f"Trend:            {result['indicators']['trend']}")
print(f"Sequence:         {result['indicators']['pattern_sequence']}")
print(f"Last Swing High:  {result['indicators']['last_swing_high']}")
print(f"Last Swing Low:   {result['indicators']['last_swing_low']}")

# Create downtrend data: Lower Highs and Lower Lows
print("\n[TEST 2] DOWNTREND - Lower Highs & Lower Lows")
print("-" * 70)

downtrend_prices = []
for i in range(300):
    # Downward trend with oscillations
    base = 200 - i * 0.2
    wave = 10 * np.sin(i / 15)
    downtrend_prices.append(base + wave)

df_down = pd.DataFrame({
    'open': downtrend_prices,
    'high': [p * 1.01 for p in downtrend_prices],
    'low': [p * 0.99 for p in downtrend_prices],
    'close': downtrend_prices,
    'volume': [1000] * len(downtrend_prices)
})

strategy2 = MTFLuxAlgo5thStrategy()

# Simulate historical analysis
for i in range(150, len(df_down), 20):
    df_subset = df_down.iloc[:i]
    result2 = strategy2.calculate(df_subset)

    if result2['indicators']['market_structure'] != "None":
        print(f"Bar {i}: {result2['indicators']['market_structure']} detected")
        print(f"  Sequence: {result2['indicators']['pattern_sequence']}")

# Final result
result2 = strategy2.calculate(df_down.iloc[:250])

print(f"\nFinal Signal:   {result2['signal']}")
print(f"Strength:       {result2['strength']}")
print(f"Reason:         {result2['reason']}")
print(f"\nMarket Structure: {result2['indicators']['market_structure']}")
print(f"Trend:            {result2['indicators']['trend']}")
print(f"Sequence:         {result2['indicators']['pattern_sequence']}")
print(f"Last Swing High:  {result2['indicators']['last_swing_high']}")
print(f"Last Swing Low:   {result2['indicators']['last_swing_low']}")

# Create ranging data
print("\n[TEST 3] RANGING MARKET")
print("-" * 70)

ranging_prices = []
for i in range(300):
    # Sideways with oscillations
    wave = 20 * np.sin(i / 10)
    ranging_prices.append(150 + wave)

df_range = pd.DataFrame({
    'open': ranging_prices,
    'high': [p * 1.01 for p in ranging_prices],
    'low': [p * 0.99 for p in ranging_prices],
    'close': ranging_prices,
    'volume': [1000] * len(ranging_prices)
})

strategy3 = MTFLuxAlgo5thStrategy()
result3 = strategy3.calculate(df_range)

print(f"Signal:   {result3['signal']}")
print(f"Strength: {result3['strength']}")
print(f"Reason:   {result3['reason']}")
print(f"\nMarket Structure: {result3['indicators']['market_structure']}")
print(f"Trend:            {result3['indicators']['trend']}")
print(f"Sequence:         {result3['indicators']['pattern_sequence']}")
print(f"Last Swing High:  {result3['indicators']['last_swing_high']}")
print(f"Last Swing Low:   {result3['indicators']['last_swing_low']}")

print("\n" + "=" * 70)
print("✓ Market structure tests complete!")
print("=" * 70)

