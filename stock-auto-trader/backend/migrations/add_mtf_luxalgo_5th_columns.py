#!/usr/bin/env python3
"""
Migration: Add MTF_LUXALGO_5TH columns to indicator_values table
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate():
    """Add new columns for MTF_LUXALGO_5TH strategy"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Add columns one by one (SQLite doesn't support adding multiple columns at once)
        columns_to_add = [
            ("volatility_score", "FLOAT"),
            ("internal_length", "INTEGER"),
            ("swing_length", "INTEGER"),
            ("market_structure", "VARCHAR(10)"),
            ("trend", "VARCHAR(10)"),
            ("pattern_sequence", "VARCHAR(100)"),
            ("pivot_internal_high", "FLOAT"),
            ("pivot_swing_high", "FLOAT"),
            ("pivot_internal_low", "FLOAT"),
            ("pivot_swing_low", "FLOAT"),
            ("last_swing_high", "FLOAT"),
            ("last_swing_low", "FLOAT"),
        ]
        
        for column_name, column_type in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE indicator_values ADD COLUMN {column_name} {column_type}"))
                conn.commit()
                print(f"✓ Added column: {column_name}")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print(f"⊘ Column already exists: {column_name}")
                else:
                    print(f"✗ Error adding column {column_name}: {e}")
    
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate()

