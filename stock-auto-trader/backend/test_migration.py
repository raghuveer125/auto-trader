#!/usr/bin/env python3
"""Test script to run the Order Block migration"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting Order Block migration test...")
print("=" * 50)

try:
    from migrations.add_order_block_columns import upgrade
    print("✅ Successfully imported migration module")
    
    print("\nRunning upgrade()...")
    upgrade()
    print("\n" + "=" * 50)
    print("Migration test completed!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

