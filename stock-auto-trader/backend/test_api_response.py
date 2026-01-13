#!/usr/bin/env python3
"""Test script to check API response for MTF_LUXALGO_5TH"""

import requests
import json

# Test the API
symbol = "SOLUSDT"
url = f"http://localhost:8000/signals/{symbol}?timeframe=1d&strategy=MTF_LUXALGO_5TH"

print(f"Testing API: {url}")
print("=" * 80)

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check if signals exist
        if 'signals' in data and len(data['signals']) > 0:
            signal = data['signals'][0]
            
            print(f"\n✅ Signal found for {symbol}")
            print(f"Strategy: {signal.get('strategy')}")
            print(f"Signal: {signal.get('signal')}")
            print(f"Strength: {signal.get('strength')}")
            print(f"Reason: {signal.get('reason')}")
            
            # Check indicators
            if 'indicators' in signal:
                indicators = signal['indicators']
                print(f"\n📊 Indicators:")
                
                # Check MTF Trends
                if 'mtf_trends' in indicators:
                    print(f"\n✅ MTF Trends found:")
                    mtf = indicators['mtf_trends']
                    for tf in ['1m', '3m', '5m', '10m', '15m', '30m', '1H', '4H', '1D']:
                        if tf in mtf:
                            trend_val = mtf[tf].get('trend', 'N/A')
                            pattern_val = mtf[tf].get('pattern', 'N/A')
                            print(f"  {tf}: trend={trend_val}, pattern={pattern_val}")
                else:
                    print(f"\n❌ MTF Trends NOT FOUND")
                
                # Check other fields
                print(f"\n📈 Other Dashboard Fields:")
                fields = [
                    'market_structure', 'trend', 'pattern_sequence',
                    'detected_pattern', 'recent_hhll', 'swing_path',
                    'zone_signal', 'zone_bias', 'context', 'confidence',
                    'trade_mode', 'countdown', 'prev_trade', 'support_stack'
                ]
                for field in fields:
                    value = indicators.get(field, 'NOT FOUND')
                    print(f"  {field}: {value}")
                
                # Save full response for inspection
                with open('api_response_sample.json', 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n✅ Full response saved to api_response_sample.json")
            else:
                print(f"\n❌ No indicators in signal")
        else:
            print(f"\n❌ No signals found in response")
            print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)

