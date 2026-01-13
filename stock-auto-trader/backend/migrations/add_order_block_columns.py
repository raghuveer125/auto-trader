"""
Migration: Add Order Block columns to indicators table
Date: 2026-01-13
Description: Adds columns for tracking bullish and bearish order blocks (demand/supply zones)
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upgrade():
    """Add Order Block columns to indicators table"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            # Add Bullish Order Block columns one by one
            logger.info("Adding bullish order block columns...")

            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_top FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_btm FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_avg FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_volume FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_time TIMESTAMP"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bull_mitigated BOOLEAN DEFAULT FALSE"))

            # Add Bearish Order Block columns one by one
            logger.info("Adding bearish order block columns...")

            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_top FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_btm FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_avg FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_volume FLOAT"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_time TIMESTAMP"))
            conn.execute(text("ALTER TABLE indicators ADD COLUMN IF NOT EXISTS ob_bear_mitigated BOOLEAN DEFAULT FALSE"))

            conn.commit()
            logger.info("✅ Successfully added Order Block columns!")
            print("✅ Migration completed successfully!")

        except Exception as e:
            logger.error(f"❌ Error adding Order Block columns: {e}")
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise

def downgrade():
    """Remove Order Block columns from indicators table"""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            logger.info("Removing order block columns...")

            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_top"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_btm"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_avg"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_volume"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_time"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bull_mitigated"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_top"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_btm"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_avg"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_volume"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_time"))
            conn.execute(text("ALTER TABLE indicators DROP COLUMN IF EXISTS ob_bear_mitigated"))

            conn.commit()
            logger.info("✅ Successfully removed Order Block columns!")
            print("✅ Downgrade completed successfully!")

        except Exception as e:
            logger.error(f"❌ Error removing Order Block columns: {e}")
            print(f"❌ Downgrade failed: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()

