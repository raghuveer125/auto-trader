#!/usr/bin/env python3
"""Check if Order Block columns exist in the database"""

from sqlalchemy import create_engine, inspect
from database import DATABASE_URL

print("Checking Order Block columns in database...")
print("=" * 60)

engine = create_engine(DATABASE_URL)
inspector = inspect(engine)

# Get all columns from indicators table
columns = inspector.get_columns('indicators')
column_names = [c['name'] for c in columns]

# Filter for OB columns
ob_columns = [name for name in column_names if 'ob_' in name]

print(f"\nTotal columns in indicators table: {len(column_names)}")
print(f"Order Block columns found: {len(ob_columns)}")

if ob_columns:
    print("\n✅ Order Block columns:")
    for col in sorted(ob_columns):
        col_info = next(c for c in columns if c['name'] == col)
        print(f"  - {col:25} {col_info['type']}")
else:
    print("\n❌ No Order Block columns found!")
    print("\nRunning migration...")
    from migrations.add_order_block_columns import upgrade
    upgrade()
    
print("\n" + "=" * 60)

