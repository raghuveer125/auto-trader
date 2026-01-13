-- Add Fair Value Gap (FVG) columns to indicator_values table
ALTER TABLE indicator_values ADD COLUMN fvg_bull_top REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bull_btm REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bull_avg REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bull_time TIMESTAMP;
ALTER TABLE indicator_values ADD COLUMN fvg_bull_mitigated BOOLEAN DEFAULT 0;

ALTER TABLE indicator_values ADD COLUMN fvg_bear_top REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bear_btm REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bear_avg REAL;
ALTER TABLE indicator_values ADD COLUMN fvg_bear_time TIMESTAMP;
ALTER TABLE indicator_values ADD COLUMN fvg_bear_mitigated BOOLEAN DEFAULT 0;

