#!/usr/bin/env python3
"""Test script to verify LuxAlgo Dashboard data structure"""

import pandas as pd
import numpy as np
import json
from strategies.mtf_luxalgo_5th import MTFLuxAlgo5thStrategy

# Create test data
np.random.seed(42)
prices = []
for i in range(200):
    wave = 100 + 20 * np.sin(i / 10) + np.random.randn() * 0.5
    prices.append(wave)

df = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=len(prices), freq='1min'),
    'open': prices,
    'high': [p * 1.01 for p in prices],
    'low': [p * 0.99 for p in prices],
    'close': prices,
    'volume': [1000 + i * 10 for i in range(len(prices))]
})

print("=" * 80)
print("LUXALGO DASHBOARD DATA STRUCTURE TEST")
print("=" * 80)

# Test strategy
strategy = MTFLuxAlgo5thStrategy()
result = strategy.calculate(df)

print(f"\nSignal: {result['signal']}")
print(f"Strength: {result['strength']}")
print(f"Reason: {result['reason']}")

print("\n" + "=" * 80)
print("DASHBOARD-SPECIFIC INDICATORS")
print("=" * 80)

indicators = result['indicators']

# Check MTF Trends
print("\n1. MTF Trends:")
if 'mtf_trends' in indicators:
    print(json.dumps(indicators['mtf_trends'], indent=2))
else:
    print("  ❌ mtf_trends NOT FOUND")

# Check Market Structure
print("\n2. Market Structure:")
print(f"  market_structure: {indicators.get('market_structure', 'NOT FOUND')}")
print(f"  trend: {indicators.get('trend', 'NOT FOUND')}")
print(f"  pattern_sequence: {indicators.get('pattern_sequence', 'NOT FOUND')}")

# Check Order Blocks
print("\n3. Order Blocks:")
if 'order_blocks' in indicators:
    ob = indicators['order_blocks']
    print(f"  Bullish OBs: {len(ob.get('bullish', []))}")
    print(f"  Bearish OBs: {len(ob.get('bearish', []))}")
    if ob.get('bullish'):
        print(f"  Latest Bullish OB: {ob['bullish'][0]}")
else:
    print("  ❌ order_blocks NOT FOUND")

# Check FVGs
print("\n4. Fair Value Gaps:")
if 'fvgs' in indicators:
    fvg = indicators['fvgs']
    print(f"  Bullish FVGs: {len(fvg.get('bullish', []))}")
    print(f"  Bearish FVGs: {len(fvg.get('bearish', []))}")
else:
    print("  ❌ fvgs NOT FOUND")

# Check Dashboard Fields
print("\n5. Dashboard Fields:")
dashboard_fields = [
    'detected_pattern', 'recent_hhll', 'swing_path', 'zone_signal',
    'zone_bias', 'context', 'confidence', 'trade_mode', 'countdown',
    'prev_trade', 'support_stack'
]
for field in dashboard_fields:
    value = indicators.get(field, 'NOT FOUND')
    print(f"  {field}: {value}")

# Check Volatility
print("\n6. Volatility Metrics:")
print(f"  volatility_score: {indicators.get('volatility_score', 'NOT FOUND')}")
print(f"  internal_length: {indicators.get('internal_length', 'NOT FOUND')}")
print(f"  swing_length: {indicators.get('swing_length', 'NOT FOUND')}")

print("\n" + "=" * 80)
print("✓ Test completed!")
print("=" * 80)

# Save sample JSON for frontend testing
sample_data = {
    'signal': result['signal'],
    'strength': result['strength'],
    'reason': result['reason'],
    'indicators': indicators
}

with open('luxalgo_sample_data.json', 'w') as f:
    json.dump(sample_data, f, indent=2, default=str)

print("\n✓ Sample data saved to luxalgo_sample_data.json")

