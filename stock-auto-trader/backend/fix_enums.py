#!/usr/bin/env python3
"""
Fix PostgreSQL enum types to use string values instead of member names.
This script will drop the existing enum types and recreate them properly.
"""

import os
from sqlalchemy import text, create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, echo=True)

def fix_enums():
    """Fix enum types in PostgreSQL"""
    with engine.connect() as conn:
        # Drop existing tables that reference the enums (in dependency order)
        print("⏳ Dropping dependent tables...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS indicator_values CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS candles CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS trades CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS strategy_settings CASCADE"))
            conn.commit()
            print("✅ Tables dropped")
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            conn.rollback()
            return

        # Drop enum types
        print("⏳ Dropping enum types...")
        try:
            conn.execute(text("DROP TYPE IF EXISTS timeframe CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS tradetype CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS strategytype CASCADE"))
            conn.commit()
            print("✅ Enum types dropped")
        except Exception as e:
            print(f"⚠️  Some enums may not exist: {e}")
            conn.rollback()

if __name__ == "__main__":
    print("🔧 Fixing PostgreSQL enum types...")
    fix_enums()
    print("\n✅ Enums cleaned up. Run `python main.py` to recreate tables with proper enum configuration.")
