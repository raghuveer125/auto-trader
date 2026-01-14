"""
MTF LuxAlgo 5th Price Action Strategy
Converted from Pine Script v5

This is a progressive conversion - functions will be added step by step
and verified visually after each addition.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from .base import BaseStrategy, Signal, to_python_type


# ============================================================================
# STEP 1-6: TYPE DEFINITIONS
# ============================================================================

@dataclass
class Bar:
    """Represents a single bar with OHLCV data"""
    o: float  # open
    c: float  # close
    h: float  # high
    l: float  # low
    v: float  # volume
    n: int    # bar_index
    t: int    # time (timestamp)
    
    @classmethod
    def from_series(cls, df: pd.DataFrame, idx: int):
        """Create Bar from DataFrame at given index"""
        return cls(
            o=df['open'].iloc[idx],
            c=df['close'].iloc[idx],
            h=df['high'].iloc[idx],
            l=df['low'].iloc[idx],
            v=df['volume'].iloc[idx],
            n=idx,
            t=int(df.index[idx].timestamp()) if hasattr(df.index[idx], 'timestamp') else idx
        )


@dataclass
class Zphl:
    """Swing high/low zone tracking"""
    top: Optional[object] = None
    bottom: Optional[object] = None
    top_label: Optional[object] = None
    bottom_label: Optional[object] = None
    stopcross: bool = True
    sbottomcross: bool = True
    itopcross: bool = True
    ibottomcross: bool = True
    txtup: str = ""
    txtdn: str = ""
    topy: float = 0.0
    bottomy: float = 0.0
    topx: float = 0.0
    bottomx: float = 0.0
    tup: float = 0.0
    tdn: float = 0.0
    tupx: int = 0
    tdnx: int = 0
    itopy: float = 0.0
    itopx: float = 0.0
    ibottomy: float = 0.0
    ibottomx: float = 0.0
    uV: float = 0.0
    dV: float = 0.0


@dataclass
class FVG:
    """Fair Value Gap"""
    box: list = None
    ln: list = None
    bull: bool = False
    top: float = 0.0
    btm: float = 0.0
    left: int = 0
    right: int = 0
    
    def __post_init__(self):
        if self.box is None:
            self.box = []
        if self.ln is None:
            self.ln = []


@dataclass
class ms:
    """Market Structure arrays"""
    p: list = None   # prices
    n: list = None   # bar indices
    l: list = None   # levels
    
    def __post_init__(self):
        if self.p is None:
            self.p = []
        if self.n is None:
            self.n = []
        if self.l is None:
            self.l = []


@dataclass
class msDraw:
    """Market Structure drawing parameters"""
    n: int = 0
    p: float = 0.0
    css: str = ""
    txt: str = ""
    bull: bool = False


@dataclass
class obC:
    """Order Block Collections"""
    top: list = None
    btm: list = None
    left: list = None
    avg: list = None
    dV: list = None
    cV: list = None
    wM: list = None
    blVP: list = None
    brVP: list = None
    dir: list = None
    h: list = None
    l: list = None
    n: list = None

    def __post_init__(self):
        for attr in ['top', 'btm', 'left', 'avg', 'dV', 'cV', 'wM',
                     'blVP', 'brVP', 'dir', 'h', 'l', 'n']:
            if getattr(self, attr) is None:
                setattr(self, attr, [])


@dataclass
class obD:
    """Order Block Drawings"""
    ob: list = None
    eOB: list = None
    blB: list = None
    brB: list = None
    mL: list = None

    def __post_init__(self):
        if self.ob is None:
            self.ob = []
        if self.eOB is None:
            self.eOB = []
        if self.blB is None:
            self.blB = []
        if self.brB is None:
            self.brB = []
        if self.mL is None:
            self.mL = []


@dataclass
class zone:
    """Accumulation/Distribution zone"""
    points: object = None
    p: float = 0.0
    c: int = 0
    t: int = 0


@dataclass
class hqlzone:
    """High/Low/Equilibrium zone visualization"""
    pbx: object = None
    ebx: object = None
    lbx: object = None
    plb: object = None
    elb: object = None
    lbl: object = None


@dataclass
class ehl:
    """External high/low"""
    pt: float = 0.0
    t: int = 0
    pb: float = 0.0
    b: int = 0


@dataclass
class pattern:
    """Pattern detection state"""
    found: str = "None"
    isfound: bool = False
    period: int = 0
    bull: bool = False


@dataclass
class OrderBlock:
    """Individual Order Block (Demand/Supply Zone)"""
    top: float = 0.0          # Upper boundary
    btm: float = 0.0          # Lower boundary
    avg: float = 0.0          # Middle line
    volume: float = 0.0       # Volume of the OB candle
    left_time: Optional[datetime] = None  # When OB was created
    left_index: int = 0       # Bar index when created
    is_bullish: bool = True   # True = demand, False = supply
    mitigated: bool = False   # Has price returned to the zone?
    structure_type: str = ""  # BOS, CHoCH, CHoCH+, or empty


@dataclass
class alerts:
    """Alert flags"""
    chochswing: bool = False
    chochplusswing: bool = False
    swingbos: bool = False
    chochplus: bool = False
    choch: bool = False
    bos: bool = False
    equal: bool = False
    ob: bool = False
    swingob: bool = False
    zone: bool = False
    fvg: bool = False
    obtouch: bool = False


# ============================================================================
# STEP 2: BOOLEAN ARRAY
# ============================================================================

# Boolean array indices (constants)
s_BOS = 0
s_CHoCH = 1
i_BOS = 2
i_CHoCH = 3
i_pp_CHoCH = 4
green_candle = 5
red_candle = 6
s_CHoCHP = 7
i_CHoCHP = 8


# ============================================================================
# STEP 11: HELPER FUNCTIONS
# ============================================================================

def f_zscore(src: pd.Series, lookback: int) -> float:
    """Calculate z-score with zero-division protection"""
    if len(src) < lookback:
        return 0.0
    dev = src.rolling(window=lookback).std().iloc[-1]
    if dev == 0 or pd.isna(dev):
        return 0.0
    sma = src.rolling(window=lookback).mean().iloc[-1]
    return (src.iloc[-1] - sma) / dev


def safe_first(arr: list):
    """Safe access to first element"""
    return arr[0] if len(arr) > 0 else None


def safe_second(arr: list):
    """Safe access to second element"""
    return arr[1] if len(arr) > 1 else None


# ============================================================================
# STEP 13: DYNAMIC LENGTH CALCULATION
# ============================================================================

def f_dynamic_length(vv: float, base_length: int, mode: str) -> int:
    """
    Calculate dynamic lookback length based on volatility score

    Args:
        vv: Volatility z-score
        base_length: Base lookback period
        mode: "auto" or "Dynamic"

    Returns:
        Adjusted lookback length
    """
    if mode != "Dynamic":
        return base_length

    # Dynamic adjustment based on volatility
    abs_vv = abs(vv)
    if abs_vv >= 2.0:
        return 5
    elif abs_vv >= 1.9:
        return 6
    elif abs_vv >= 1.8:
        return 7
    elif abs_vv >= 1.7:
        return 8
    elif abs_vv >= 1.6:
        return 9
    else:
        return 10


# ============================================================================
# STEP 14: PIVOT CALCULATIONS
# ============================================================================

def f_pivothigh(series: pd.Series, left_bars: int, right_bars: int) -> Optional[float]:
    """
    Detect pivot high - a local maximum

    Pine Script equivalent: ta.pivothigh(high, left_bars, right_bars)

    Returns the value of the pivot high if found at the position
    (current_index - right_bars), otherwise returns None.

    Args:
        series: Price series (typically 'high')
        left_bars: Number of bars to the left
        right_bars: Number of bars to the right

    Returns:
        Pivot high value or None
    """
    if len(series) < left_bars + right_bars + 1:
        return None

    # Check position: current_index - right_bars
    pivot_idx = len(series) - 1 - right_bars
    if pivot_idx < left_bars:
        return None

    pivot_value = series.iloc[pivot_idx]

    # Check if it's higher than all bars to the left
    for i in range(pivot_idx - left_bars, pivot_idx):
        if series.iloc[i] >= pivot_value:
            return None

    # Check if it's higher than all bars to the right
    for i in range(pivot_idx + 1, pivot_idx + right_bars + 1):
        if i >= len(series):
            return None
        if series.iloc[i] >= pivot_value:
            return None

    return float(pivot_value)


def f_pivotlow(series: pd.Series, left_bars: int, right_bars: int) -> Optional[float]:
    """
    Detect pivot low - a local minimum

    Pine Script equivalent: ta.pivotlow(low, left_bars, right_bars)

    Returns the value of the pivot low if found at the position
    (current_index - right_bars), otherwise returns None.

    Args:
        series: Price series (typically 'low')
        left_bars: Number of bars to the left
        right_bars: Number of bars to the right

    Returns:
        Pivot low value or None
    """
    if len(series) < left_bars + right_bars + 1:
        return None

    # Check position: current_index - right_bars
    pivot_idx = len(series) - 1 - right_bars
    if pivot_idx < left_bars:
        return None

    pivot_value = series.iloc[pivot_idx]

    # Check if it's lower than all bars to the left
    for i in range(pivot_idx - left_bars, pivot_idx):
        if series.iloc[i] <= pivot_value:
            return None

    # Check if it's lower than all bars to the right
    for i in range(pivot_idx + 1, pivot_idx + right_bars + 1):
        if i >= len(series):
            return None
        if series.iloc[i] <= pivot_value:
            return None

    return float(pivot_value)


# ============================================================================
# STEP 14: PIVOT CALCULATIONS
# ============================================================================

def f_pivothigh(series: pd.Series, left_bars: int, right_bars: int) -> Optional[float]:
    """
    Detect pivot high - a local maximum

    Pine Script equivalent: ta.pivothigh(high, left_bars, right_bars)

    Returns the value of the pivot high if found at the position
    (current_index - right_bars), otherwise returns None.

    Args:
        series: Price series (typically 'high')
        left_bars: Number of bars to the left
        right_bars: Number of bars to the right

    Returns:
        Pivot high value or None
    """
    if len(series) < left_bars + right_bars + 1:
        return None

    # Check position: current_index - right_bars
    pivot_idx = len(series) - 1 - right_bars
    if pivot_idx < left_bars:
        return None

    pivot_value = series.iloc[pivot_idx]

    # Check if it's higher than all bars to the left
    for i in range(pivot_idx - left_bars, pivot_idx):
        if series.iloc[i] >= pivot_value:
            return None

    # Check if it's higher than all bars to the right
    for i in range(pivot_idx + 1, pivot_idx + right_bars + 1):
        if i >= len(series):
            return None
        if series.iloc[i] >= pivot_value:
            return None

    return float(pivot_value)


def f_pivotlow(series: pd.Series, left_bars: int, right_bars: int) -> Optional[float]:
    """
    Detect pivot low - a local minimum

    Pine Script equivalent: ta.pivotlow(low, left_bars, right_bars)

    Returns the value of the pivot low if found at the position
    (current_index - right_bars), otherwise returns None.

    Args:
        series: Price series (typically 'low')
        left_bars: Number of bars to the left
        right_bars: Number of bars to the right

    Returns:
        Pivot low value or None
    """
    if len(series) < left_bars + right_bars + 1:
        return None

    # Check position: current_index - right_bars
    pivot_idx = len(series) - 1 - right_bars
    if pivot_idx < left_bars:
        return None

    pivot_value = series.iloc[pivot_idx]

    # Check if it's lower than all bars to the left
    for i in range(pivot_idx - left_bars, pivot_idx):
        if series.iloc[i] <= pivot_value:
            return None

    # Check if it's lower than all bars to the right
    for i in range(pivot_idx + 1, pivot_idx + right_bars + 1):
        if i >= len(series):
            return None
        if series.iloc[i] <= pivot_value:
            return None

    return float(pivot_value)


# ============================================================================
# STEP 16: MARKET STRUCTURE CONSTANTS
# ============================================================================

MS_BOS = "BOS"
MS_CHOCH = "CHoCH"
MS_CHOCHP = "CHoCH+"


# ============================================================================
# STEP 16: ORDER BLOCK DETECTION
# ============================================================================

def detect_order_block(
    df: pd.DataFrame,
    pivot_index: int,
    is_bullish: bool,
    lookback_length: int,
    positioning: str = "Precise"
) -> Optional[OrderBlock]:
    """
    Detect Order Block (Demand/Supply Zone) based on pivot point

    Logic from Pine Script:
    - Bullish OB: Find candle with lowest low before pivot high
    - Bearish OB: Find candle with highest high before pivot low

    Args:
        df: DataFrame with OHLCV data
        pivot_index: Index where pivot was detected
        is_bullish: True for bullish OB (demand), False for bearish OB (supply)
        lookback_length: How many bars to look back from pivot
        positioning: "Full", "Middle", "Accurate", or "Precise"

    Returns:
        OrderBlock object or None if cannot be detected
    """
    # Ensure we have enough data
    if pivot_index < lookback_length:
        return None

    # Get the range of candles to analyze
    start_idx = max(0, pivot_index - lookback_length)
    end_idx = pivot_index

    if start_idx >= end_idx:
        return None

    # Extract the range
    range_df = df.iloc[start_idx:end_idx + 1]

    if len(range_df) == 0:
        return None

    try:
        if is_bullish:
            # Bullish OB: Find candle with lowest low
            ob_idx_relative = range_df['low'].idxmin()
            ob_idx = df.index.get_loc(ob_idx_relative)
            ob_candle = df.iloc[ob_idx]

            # Determine boundaries based on positioning
            if positioning == "Full":
                top = ob_candle['high']
                btm = ob_candle['low']
            elif positioning == "Middle":
                top = (ob_candle['open'] + ob_candle['close'] + ob_candle['high'] + ob_candle['low']) / 4
                btm = ob_candle['low']
            else:  # Accurate or Precise
                top = (ob_candle['high'] + ob_candle['low']) / 2
                btm = ob_candle['low']

                # Precise: Adjust top to body if needed
                if positioning == "Precise":
                    body_top = max(ob_candle['open'], ob_candle['close'])
                    avg = (top + btm) / 2
                    if avg < body_top:
                        top = avg

        else:
            # Bearish OB: Find candle with highest high
            ob_idx_relative = range_df['high'].idxmax()
            ob_idx = df.index.get_loc(ob_idx_relative)
            ob_candle = df.iloc[ob_idx]

            # Determine boundaries based on positioning
            if positioning == "Full":
                top = ob_candle['high']
                btm = ob_candle['low']
            elif positioning == "Middle":
                top = ob_candle['high']
                btm = (ob_candle['open'] + ob_candle['close'] + ob_candle['high'] + ob_candle['low']) / 4
            else:  # Accurate or Precise
                top = ob_candle['high']
                btm = (ob_candle['high'] + ob_candle['low']) / 2

                # Precise: Adjust btm to body if needed
                if positioning == "Precise":
                    body_btm = min(ob_candle['open'], ob_candle['close'])
                    avg = (top + btm) / 2
                    if avg > body_btm:
                        btm = avg

        # Calculate average (middle line)
        avg = (top + btm) / 2

        # Get timestamp
        ob_time = df.index[ob_idx] if hasattr(df.index[ob_idx], 'to_pydatetime') else None
        if ob_time and hasattr(ob_time, 'to_pydatetime'):
            ob_time = ob_time.to_pydatetime()

        # Create OrderBlock
        return OrderBlock(
            top=float(top),
            btm=float(btm),
            avg=float(avg),
            volume=float(ob_candle['volume']),
            left_time=ob_time,
            left_index=ob_idx,
            is_bullish=is_bullish,
            mitigated=False,
            structure_type=""  # Will be set by caller based on market structure
        )

    except Exception as e:
        # Silently fail if there's any issue
        return None


# ============================================================================
# STEP 18: ACCUMULATION/DISTRIBUTION ZONES
# ============================================================================

@dataclass
class ZonePivot:
    """Zone pivot point"""
    price: float
    time: datetime
    direction: int  # 1 for high, -1 for low


class ZoneDetector:
    """Detects Accumulation and Distribution zones"""
    def __init__(self, mode: str = "Fast", valid_bars: int = 300):
        self.mode = mode  # "Fast" or "Slow"
        self.valid_bars = valid_bars
        self.pivots: List[ZonePivot] = []
        self.last_zone_found = ""
        self.last_zone_bull = None
        self.last_zone_bar = None
        self.zone_high = None
        self.zone_low = None

    def add_pivot(self, price: float, time: datetime, direction: int):
        """Add a pivot point"""
        self.pivots.insert(0, ZonePivot(price, time, direction))

        # Keep only last 7 pivots
        if len(self.pivots) > 7:
            self.pivots = self.pivots[:7]

        # Clear if same direction consecutive
        if len(self.pivots) > 1 and self.pivots[0].direction == self.pivots[1].direction:
            self.pivots.clear()

    def detect_zone(self, current_bar: int) -> Tuple[str, bool, float, float]:
        """
        Detect accumulation or distribution zone
        Returns: (zone_type, is_bullish, zone_high, zone_low)
        """
        # Check expiry
        if self.last_zone_bar and current_bar - self.last_zone_bar > self.valid_bars:
            self.reset_zone()

        zone_found = ""
        zone_bull = None
        z_high = None
        z_low = None

        if self.mode == "Slow":
            # Need 6 pivots: L-H-L-H-L-H (accumulation) or H-L-H-L-H-L (distribution)
            if len(self.pivots) >= 6:
                # Accumulation: descending lows, ascending highs
                if (self.pivots[0].direction == -1 and self.pivots[1].direction == 1 and
                    self.pivots[2].direction == -1 and self.pivots[3].direction == 1 and
                    self.pivots[4].direction == -1 and self.pivots[5].direction == 1):

                    if (self.pivots[0].price > self.pivots[2].price > self.pivots[4].price and
                        self.pivots[1].price < self.pivots[3].price < self.pivots[5].price):
                        zone_found = "Accumulation Zone"
                        zone_bull = True
                        z_high = self.pivots[3].price
                        z_low = self.pivots[2].price
                        self.pivots.clear()

                # Distribution: ascending highs, descending lows
                elif (self.pivots[0].direction == 1 and self.pivots[1].direction == -1 and
                      self.pivots[2].direction == 1 and self.pivots[3].direction == -1 and
                      self.pivots[4].direction == 1 and self.pivots[5].direction == -1):

                    if (self.pivots[0].price < self.pivots[2].price < self.pivots[4].price and
                        self.pivots[1].price > self.pivots[3].price > self.pivots[5].price):
                        zone_found = "Distribution Zone"
                        zone_bull = False
                        z_high = self.pivots[2].price
                        z_low = self.pivots[3].price
                        self.pivots.clear()

        else:  # Fast mode
            # Need 4 pivots: L-H-L-H (accumulation) or H-L-H-L (distribution)
            if len(self.pivots) >= 4:
                # Accumulation
                if (self.pivots[0].direction == -1 and self.pivots[1].direction == 1 and
                    self.pivots[2].direction == -1 and self.pivots[3].direction == 1):

                    if (self.pivots[0].price > self.pivots[2].price and
                        self.pivots[1].price < self.pivots[3].price):
                        zone_found = "Accumulation Zone"
                        zone_bull = True
                        z_high = self.pivots[3].price
                        z_low = self.pivots[2].price
                        self.pivots.clear()

                # Distribution
                elif (self.pivots[0].direction == 1 and self.pivots[1].direction == -1 and
                      self.pivots[2].direction == 1 and self.pivots[3].direction == -1):

                    if (self.pivots[0].price < self.pivots[2].price and
                        self.pivots[1].price > self.pivots[3].price):
                        zone_found = "Distribution Zone"
                        zone_bull = False
                        z_high = self.pivots[2].price
                        z_low = self.pivots[3].price
                        self.pivots.clear()

        # Store zone if detected
        if zone_found:
            self.last_zone_found = zone_found
            self.last_zone_bull = zone_bull
            self.last_zone_bar = current_bar
            self.zone_high = z_high
            self.zone_low = z_low

        return zone_found, zone_bull, z_high, z_low

    def reset_zone(self):
        """Reset zone state"""
        self.last_zone_found = ""
        self.last_zone_bull = None
        self.last_zone_bar = None
        self.zone_high = None
        self.zone_low = None


# ============================================================================
# STEP 16B: FAIR VALUE GAP (FVG) DETECTION
# ============================================================================

@dataclass
class FVG:
    """Fair Value Gap data structure"""
    top: float
    btm: float
    avg: float
    left_time: Optional[datetime] = None
    mitigated: bool = False
    gap_type: str = ""  # "FVG", "IFVG", "BISI", "SIBI"


def detect_fvg(df: pd.DataFrame, index: int, is_bullish: bool, fvg_type: str = "FVG") -> Optional[FVG]:
    """
    Detect Fair Value Gap at given index

    Bullish FVG: Gap between candle[i-2].high and candle[i].low (candle[i-1] doesn't fill it)
    Bearish FVG: Gap between candle[i-2].low and candle[i].high (candle[i-1] doesn't fill it)
    """
    if index < 2 or index >= len(df):
        return None

    try:
        if is_bullish:
            # Bullish FVG: candle[i-2].high < candle[i].low
            high_2 = df.iloc[index - 2]['high']
            low_0 = df.iloc[index]['low']
            high_1 = df.iloc[index - 1]['high']
            low_1 = df.iloc[index - 1]['low']

            # Check if there's a gap
            if high_2 < low_0:
                # Verify middle candle doesn't fill the gap
                if high_1 < low_0 and low_1 > high_2:
                    return FVG(
                        top=low_0,
                        btm=high_2,
                        avg=(low_0 + high_2) / 2,
                        left_time=df.iloc[index - 2]['timestamp'],
                        gap_type=fvg_type
                    )
        else:
            # Bearish FVG: candle[i-2].low > candle[i].high
            low_2 = df.iloc[index - 2]['low']
            high_0 = df.iloc[index]['high']
            high_1 = df.iloc[index - 1]['high']
            low_1 = df.iloc[index - 1]['low']

            # Check if there's a gap
            if low_2 > high_0:
                # Verify middle candle doesn't fill the gap
                if low_1 > high_0 and high_1 < low_2:
                    return FVG(
                        top=low_2,
                        btm=high_0,
                        avg=(low_2 + high_0) / 2,
                        left_time=df.iloc[index - 2]['timestamp'],
                        gap_type=fvg_type
                    )

        return None
    except Exception:
        return None


class FVGManager:
    """Manages active Fair Value Gaps and handles mitigation"""
    def __init__(self, max_fvgs: int = 5, mitigation_src: str = "Close"):
        self.bullish_fvgs: List[FVG] = []
        self.bearish_fvgs: List[FVG] = []
        self.max_fvgs = max_fvgs
        self.mitigation_src = mitigation_src  # "Close", "Wick", "Average"

    def add_bullish_fvg(self, fvg: FVG):
        if fvg:
            self.bullish_fvgs.insert(0, fvg)
            if len(self.bullish_fvgs) > self.max_fvgs:
                self.bullish_fvgs = self.bullish_fvgs[:self.max_fvgs]

    def add_bearish_fvg(self, fvg: FVG):
        if fvg:
            self.bearish_fvgs.insert(0, fvg)
            if len(self.bearish_fvgs) > self.max_fvgs:
                self.bearish_fvgs = self.bearish_fvgs[:self.max_fvgs]

    def check_mitigation(self, current_close: float, current_high: float, current_low: float):
        """Check if any FVGs have been mitigated"""
        self.bullish_fvgs = [
            fvg for fvg in self.bullish_fvgs
            if not self._is_mitigated(fvg, current_close, current_high, current_low, True)
        ]

        self.bearish_fvgs = [
            fvg for fvg in self.bearish_fvgs
            if not self._is_mitigated(fvg, current_close, current_high, current_low, False)
        ]

    def _is_mitigated(self, fvg: FVG, close: float, high: float, low: float, is_bullish: bool) -> bool:
        """Check if FVG is mitigated based on mitigation source"""
        if self.mitigation_src == "Close":
            return close < fvg.btm if is_bullish else close > fvg.top
        elif self.mitigation_src == "Wick":
            return low < fvg.btm if is_bullish else high > fvg.top
        else:  # Average
            return close < fvg.avg if is_bullish else close > fvg.avg

    def get_latest_bullish(self) -> Optional[FVG]:
        return self.bullish_fvgs[0] if self.bullish_fvgs else None

    def get_latest_bearish(self) -> Optional[FVG]:
        return self.bearish_fvgs[0] if self.bearish_fvgs else None


class OrderBlockManager:
    """
    Manages active Order Blocks and handles mitigation

    Tracks up to max_blocks bullish and bearish order blocks
    Removes blocks when price mitigates them
    """
    def __init__(self, max_blocks: int = 5, mitigation_mode: str = "Absolute"):
        self.bullish_blocks: List[OrderBlock] = []
        self.bearish_blocks: List[OrderBlock] = []
        self.max_blocks = max_blocks
        self.mitigation_mode = mitigation_mode  # "Absolute" or "Middle"

    def add_bullish_block(self, ob: OrderBlock):
        """Add a bullish order block (demand zone)"""
        if ob is None:
            return

        # Add to front of list
        self.bullish_blocks.insert(0, ob)

        # Keep only max_blocks
        if len(self.bullish_blocks) > self.max_blocks:
            self.bullish_blocks = self.bullish_blocks[:self.max_blocks]

    def add_bearish_block(self, ob: OrderBlock):
        """Add a bearish order block (supply zone)"""
        if ob is None:
            return

        # Add to front of list
        self.bearish_blocks.insert(0, ob)

        # Keep only max_blocks
        if len(self.bearish_blocks) > self.max_blocks:
            self.bearish_blocks = self.bearish_blocks[:self.max_blocks]

    def check_mitigation(self, current_close: float):
        """
        Check if any order blocks have been mitigated by current price

        Mitigation logic:
        - Absolute: Price crosses the bottom (bull) or top (bear)
        - Middle: Price crosses the middle line
        """
        # Check bullish blocks (demand zones)
        self.bullish_blocks = [
            ob for ob in self.bullish_blocks
            if not self._is_mitigated(ob, current_close, is_bullish=True)
        ]

        # Check bearish blocks (supply zones)
        self.bearish_blocks = [
            ob for ob in self.bearish_blocks
            if not self._is_mitigated(ob, current_close, is_bullish=False)
        ]

    def _is_mitigated(self, ob: OrderBlock, current_close: float, is_bullish: bool) -> bool:
        """Check if an order block is mitigated"""
        if self.mitigation_mode == "Middle":
            # Mitigated if price crosses middle line
            if is_bullish:
                return current_close < ob.avg
            else:
                return current_close > ob.avg
        else:  # Absolute
            # Mitigated if price crosses bottom (bull) or top (bear)
            if is_bullish:
                return current_close < ob.btm
            else:
                return current_close > ob.top

    def get_active_blocks(self) -> Tuple[List[OrderBlock], List[OrderBlock]]:
        """Get all active order blocks"""
        return self.bullish_blocks, self.bearish_blocks

    def get_latest_bullish(self) -> Optional[OrderBlock]:
        """Get the most recent bullish order block"""
        return self.bullish_blocks[0] if self.bullish_blocks else None

    def get_latest_bearish(self) -> Optional[OrderBlock]:
        """Get the most recent bearish order block"""
        return self.bearish_blocks[0] if self.bearish_blocks else None


# ============================================================================
# STEP 15: MARKET STRUCTURE DETECTION
# ============================================================================

class MarketStructure:
    """
    Market structure state and detection

    Tracks:
    - HH (Higher High) - Bullish continuation
    - HL (Higher Low) - Bullish pullback
    - LH (Lower High) - Bearish pullback
    - LL (Lower Low) - Bearish continuation
    """
    def __init__(self):
        self.last_high: Optional[float] = None
        self.last_low: Optional[float] = None
        self.last_major: Optional[str] = None  # "HH", "HL", "LH", "LL"
        self.last_major_price: Optional[float] = None
        self.sequence: str = ""
        self.last_struct: str = ""

    def update_high(self, pivot_high: float) -> Optional[str]:
        """
        Update with new pivot high and determine structure

        Returns:
            Structure type: "HH", "HL", or None
        """
        if self.last_high is None:
            self.last_high = pivot_high
            return None

        # Compare with previous high
        if pivot_high > self.last_high:
            # Higher High - bullish
            struct = "HH"
            self.last_major = "HH"
            self.last_major_price = pivot_high 
            self.sequence = "HH"
            self.last_struct = "HH"
        else:
            # Higher Low (lower than last high but still a high pivot)
            struct = "HL"
            if self.last_struct != "HL":
                self.sequence = "HL" if self.sequence == "" else f"{self.sequence} → HL"
                self.last_struct = "HL"

        self.last_high = pivot_high
        return struct

    def update_low(self, pivot_low: float) -> Optional[str]:
        """
        Update with new pivot low and determine structure

        Returns:
            Structure type: "LL", "LH", or None
        """
        if self.last_low is None:
            self.last_low = pivot_low
            return None

        # Compare with previous low
        if pivot_low < self.last_low:
            # Lower Low - bearish
            struct = "LL"
            self.last_major = "LL"
            self.last_major_price = pivot_low
            self.sequence = "LL"
            self.last_struct = "LL"
        else:
            # Lower High (higher than last low but still a low pivot)
            struct = "LH"
            if self.last_struct != "LH":
                self.sequence = "LH" if self.sequence == "" else f"{self.sequence} → LH"
                self.last_struct = "LH"

        self.last_low = pivot_low
        return struct


    def get_trend(self) -> int:
        """
        Get current trend direction

        Returns:
            1 for bullish (HH/HL), -1 for bearish (LL/LH), 0 for neutral
        """
        if self.last_major in ["HH", "HL"]:
            return 1
        elif self.last_major in ["LL", "LH"]:
            return -1
        return 0


# ============================================================================
# MAIN STRATEGY CLASS
# ============================================================================

class MTFLuxAlgo5thStrategy(BaseStrategy):
    """
    MTF LuxAlgo 5th Price Action Strategy

    Progressive conversion from Pine Script - functions added incrementally
    """

    name = "MTF_LUXALGO_5TH"
    description = "Multi-Timeframe LuxAlgo 5th Price Action (Progressive Build)"

    def __init__(self):
        """Initialize with default parameters"""
        # User inputs - Market Structure
        self.show_swing_ms = "All"
        self.show_internal_ms = "All"
        self.internal_r_lookback = 5
        self.swing_r_lookback = 50
        self.ms_mode = "auto"  # "auto" or "Dynamic"

        # User inputs - Display options
        self.show_mtf_str = True
        self.show_eql = False
        self.plotcandle_bool = False
        self.barcolor_bool = False

        # User inputs - Order Blocks
        self.ob_show = True
        self.ob_num = 5
        self.ob_metrics_show = True
        self.ob_swings = False
        self.ob_filter = "None"
        self.ob_mitigation = "Absolute"
        self.ob_pos = "Precise"
        self.use_grayscale = False
        self.use_show_metric = True
        self.use_middle_line = True
        self.use_overlap = True
        self.use_overlap_method = "Previous"

        # User inputs - Zones
        self.show_acc_dist_zone = False
        self.zone_mode = "Fast"

        # User inputs - High/Low
        self.show_lbl = True
        self.show_mtb = True

        # User inputs - FVG
        self.fvg_enable = False
        self.what_fvg = "FVG"
        self.fvg_num = 5
        self.fvg_extend = 10
        self.fvg_src = "Close"

        # State variables
        self.pattern_state = pattern()
        self.sLen = self.swing_r_lookback

        # Market structure tracking
        self.market_structure = MarketStructure()

        # Order Block tracking
        self.ob_manager = OrderBlockManager(
            max_blocks=self.ob_num,
            mitigation_mode=self.ob_mitigation
        )

        # FVG tracking
        self.fvg_manager = FVGManager(
            max_fvgs=self.fvg_num,
            mitigation_src=self.fvg_src
        )

        # Zone tracking
        self.zone_detector = ZoneDetector(
            mode=self.zone_mode,
            valid_bars=300
        )

        # Zone signal state
        self.acc_high = None
        self.acc_low = None
        self.dist_high = None
        self.dist_low = None
        self.acc_break_prev = False
        self.dist_break_prev = False

    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate trading signal

        Currently implements:
        - Step 1-6: Type definitions ✓
        - Step 11: Helper functions ✓
        - Step 12: General setup ✓
        - Step 13: Dynamic length ✓
        """
        if len(df) < self.swing_r_lookback + 10:
            return self.get_result(
                Signal.HOLD,
                0,
                "Insufficient data for MTF LuxAlgo calculation",
                {}
            )

        # ============================================================
        # STEP 12: GENERAL SETUP
        # ============================================================

        # Initialize boolean array
        boolean = [False] * 9

        # Create current bar
        b = Bar.from_series(df, len(df) - 1)

        # Update pattern state
        if self.pattern_state.isfound:
            self.pattern_state.period += 1
            if self.pattern_state.period == 50:
                self.pattern_state.period = 0
                self.pattern_state.found = "None"
                self.pattern_state.isfound = False
                self.pattern_state.bull = False

        # Set candle color flags
        if b.c > b.o:
            boolean[green_candle] = True
        elif b.c < b.o:
            boolean[red_candle] = True

        # ============================================================
        # STEP 13: DYNAMIC LENGTH CALCULATION
        # ============================================================

        # Calculate volatility score
        close_series = df['close']
        price_change_pct = ((close_series - close_series.shift(self.internal_r_lookback))
                           / close_series.shift(self.internal_r_lookback) * 100)
        vv = f_zscore(price_change_pct, self.internal_r_lookback)

        # Calculate dynamic internal length
        iLen = f_dynamic_length(vv, self.internal_r_lookback, self.ms_mode)

        # Swing length (static for now)
        sLen = self.sLen

        # ============================================================
        # STEP 14: PIVOT DETECTION
        # ============================================================

        # Calculate pivots using internal and swing lengths
        # Pine: iH = ta.pivothigh(high, iLen, iLen)
        iH = f_pivothigh(df['high'], iLen, iLen)  # Internal pivot high
        sH = f_pivothigh(df['high'], sLen, sLen)  # Swing pivot high
        iL = f_pivotlow(df['low'], iLen, iLen)    # Internal pivot low
        sL = f_pivotlow(df['low'], sLen, sLen)    # Swing pivot low

        # ============================================================
        # STEP 15: MARKET STRUCTURE DETECTION
        # ============================================================

        # Update market structure with swing pivots
        high_struct = None
        low_struct = None

        if sH is not None:
            high_struct = self.market_structure.update_high(sH)

        if sL is not None:
            low_struct = self.market_structure.update_low(sL)

        # Get current trend
        trend = self.market_structure.get_trend()

        # Determine if we have a structure break
        structure_type = high_struct or low_struct or self.market_structure.last_struct

        # ============================================================
        # STEP 16: ORDER BLOCK DETECTION
        # ============================================================

        # Detect Order Blocks when internal pivots are found
        # Bullish OB: Created at internal pivot high
        if iH is not None and self.ob_show:
            current_idx = len(df) - 1
            pivot_idx = current_idx - iLen  # Pivot is iLen bars back

            # Detect bullish order block
            bull_ob = detect_order_block(
                df=df,
                pivot_index=pivot_idx,
                is_bullish=True,
                lookback_length=iLen,
                positioning=self.ob_pos
            )

            if bull_ob:
                # Set structure type based on market structure
                bull_ob.structure_type = structure_type or ""
                self.ob_manager.add_bullish_block(bull_ob)

        # Bearish OB: Created at internal pivot low
        if iL is not None and self.ob_show:
            current_idx = len(df) - 1
            pivot_idx = current_idx - iLen  # Pivot is iLen bars back

            # Detect bearish order block
            bear_ob = detect_order_block(
                df=df,
                pivot_index=pivot_idx,
                is_bullish=False,
                lookback_length=iLen,
                positioning=self.ob_pos
            )

            if bear_ob:
                # Set structure type based on market structure
                bear_ob.structure_type = structure_type or ""
                self.ob_manager.add_bearish_block(bear_ob)

        # Check for mitigation of existing order blocks
        self.ob_manager.check_mitigation(b.c)

        # Get active order blocks
        bullish_obs, bearish_obs = self.ob_manager.get_active_blocks()
        latest_bull_ob = self.ob_manager.get_latest_bullish()
        latest_bear_ob = self.ob_manager.get_latest_bearish()

        # ============================================================
        # STEP 17: FAIR VALUE GAP (FVG) DETECTION
        # ============================================================

        if self.fvg_enable:
            current_idx = len(df) - 1

            # Detect bullish FVG
            bull_fvg = detect_fvg(df, current_idx, is_bullish=True, fvg_type=self.what_fvg)
            if bull_fvg:
                self.fvg_manager.add_bullish_fvg(bull_fvg)

            # Detect bearish FVG
            bear_fvg = detect_fvg(df, current_idx, is_bullish=False, fvg_type=self.what_fvg)
            if bear_fvg:
                self.fvg_manager.add_bearish_fvg(bear_fvg)

            # Check mitigation
            self.fvg_manager.check_mitigation(b.c, b.h, b.l)

        # Get active FVGs
        latest_bull_fvg = self.fvg_manager.get_latest_bullish()
        latest_bear_fvg = self.fvg_manager.get_latest_bearish()

        # ============================================================
        # STEP 18: ZONE DETECTION
        # ============================================================

        zone_found = ""
        zone_bull = None
        zone_high = None
        zone_low = None
        accumulation_buy_signal = False
        distribution_sell_signal = False

        if self.show_acc_dist_zone:
            # Add pivots to zone detector
            if iH is not None:
                pivot_time = df.iloc[len(df) - 1 - iLen]['timestamp']
                self.zone_detector.add_pivot(iH, pivot_time, 1)

            if iL is not None:
                pivot_time = df.iloc[len(df) - 1 - iLen]['timestamp']
                self.zone_detector.add_pivot(iL, pivot_time, -1)

            # Detect zone
            current_bar_idx = len(df) - 1
            zone_found, zone_bull, zone_high, zone_low = self.zone_detector.detect_zone(current_bar_idx)

            # Update zone ranges
            if self.zone_detector.last_zone_found == "Accumulation Zone":
                self.acc_high = self.zone_detector.zone_high
                self.acc_low = self.zone_detector.zone_low

            if self.zone_detector.last_zone_found == "Distribution Zone":
                self.dist_high = self.zone_detector.zone_high
                self.dist_low = self.zone_detector.zone_low

            # Accumulation breakout logic
            acc_break = False
            if self.zone_detector.last_zone_found == "Accumulation Zone" and self.acc_high:
                acc_break = b.c > self.acc_high

            acc_retest = self.acc_break_prev and b.l <= self.acc_high and b.c > self.acc_high
            accumulation_buy_signal = self.acc_break_prev and acc_retest
            self.acc_break_prev = acc_break

            # Distribution breakdown logic
            dist_break = False
            if self.zone_detector.last_zone_found == "Distribution Zone" and self.dist_low:
                dist_break = b.c < self.dist_low

            dist_retest = self.dist_break_prev and b.h >= self.dist_low and b.c < self.dist_low
            distribution_sell_signal = self.dist_break_prev and dist_retest
            self.dist_break_prev = dist_break

        # ============================================================
        # OUTPUT INDICATORS
        # ============================================================

        # Calculate historical data for plotting (last 100 points)
        plot_length = min(100, len(df))
        df_plot = df.tail(plot_length)

        indicators = {
            # Current values
            "volatility_score": to_python_type(round(vv, 4)),
            "internal_length": to_python_type(iLen),
            "swing_length": to_python_type(sLen),
            "current_close": to_python_type(round(b.c, 2)),
            "current_volume": to_python_type(round(b.v, 0)),
            "bar_index": to_python_type(b.n),
            "is_green_candle": to_python_type(boolean[green_candle]),
            "is_red_candle": to_python_type(boolean[red_candle]),
            "ms_mode": self.ms_mode,

            # Pivot values
            "pivot_internal_high": float(round(iH, 2)) if iH is not None else None,
            "pivot_swing_high": float(round(sH, 2)) if sH is not None else None,
            "pivot_internal_low": float(round(iL, 2)) if iL is not None else None,
            "pivot_swing_low": float(round(sL, 2)) if sL is not None else None,

            # Market structure
            "market_structure": structure_type or "None",
            "trend": "Bullish" if trend > 0 else "Bearish" if trend < 0 else "Neutral",
            "pattern_sequence": self.market_structure.sequence,
            "last_swing_high": float(round(self.market_structure.last_high, 2)) if self.market_structure.last_high else None,
            "last_swing_low": float(round(self.market_structure.last_low, 2)) if self.market_structure.last_low else None,

            # Order Blocks - Latest (for database storage)
            "ob_bull_top": float(round(latest_bull_ob.top, 2)) if latest_bull_ob else None,
            "ob_bull_btm": float(round(latest_bull_ob.btm, 2)) if latest_bull_ob else None,
            "ob_bull_avg": float(round(latest_bull_ob.avg, 2)) if latest_bull_ob else None,
            "ob_bull_volume": float(round(latest_bull_ob.volume, 0)) if latest_bull_ob else None,
            "ob_bull_time": latest_bull_ob.left_time if latest_bull_ob else None,
            "ob_bull_mitigated": latest_bull_ob.mitigated if latest_bull_ob else False,

            "ob_bear_top": float(round(latest_bear_ob.top, 2)) if latest_bear_ob else None,
            "ob_bear_btm": float(round(latest_bear_ob.btm, 2)) if latest_bear_ob else None,
            "ob_bear_avg": float(round(latest_bear_ob.avg, 2)) if latest_bear_ob else None,
            "ob_bear_volume": float(round(latest_bear_ob.volume, 0)) if latest_bear_ob else None,
            "ob_bear_time": latest_bear_ob.left_time if latest_bear_ob else None,
            "ob_bear_mitigated": latest_bear_ob.mitigated if latest_bear_ob else False,

            # FVG - Latest (for database storage)
            "fvg_bull_top": float(round(latest_bull_fvg.top, 2)) if latest_bull_fvg else None,
            "fvg_bull_btm": float(round(latest_bull_fvg.btm, 2)) if latest_bull_fvg else None,
            "fvg_bull_avg": float(round(latest_bull_fvg.avg, 2)) if latest_bull_fvg else None,
            "fvg_bull_time": latest_bull_fvg.left_time if latest_bull_fvg else None,
            "fvg_bull_mitigated": latest_bull_fvg.mitigated if latest_bull_fvg else False,

            "fvg_bear_top": float(round(latest_bear_fvg.top, 2)) if latest_bear_fvg else None,
            "fvg_bear_btm": float(round(latest_bear_fvg.btm, 2)) if latest_bear_fvg else None,
            "fvg_bear_avg": float(round(latest_bear_fvg.avg, 2)) if latest_bear_fvg else None,
            "fvg_bear_time": latest_bear_fvg.left_time if latest_bear_fvg else None,
            "fvg_bear_mitigated": latest_bear_fvg.mitigated if latest_bear_fvg else False,

            # Order Blocks - All active (for frontend visualization)
            "order_blocks": {
                "bullish": [
                    {
                        "top": float(round(ob.top, 2)),
                        "btm": float(round(ob.btm, 2)),
                        "avg": float(round(ob.avg, 2)),
                        "volume": float(round(ob.volume, 0)),
                        "time": str(ob.left_time) if ob.left_time else None,
                        "structure": ob.structure_type,
                        "mitigated": ob.mitigated
                    }
                    for ob in bullish_obs
                ],
                "bearish": [
                    {
                        "top": float(round(ob.top, 2)),
                        "btm": float(round(ob.btm, 2)),
                        "avg": float(round(ob.avg, 2)),
                        "volume": float(round(ob.volume, 0)),
                        "time": str(ob.left_time) if ob.left_time else None,
                        "structure": ob.structure_type,
                        "mitigated": ob.mitigated
                    }
                    for ob in bearish_obs
                ]
            },

            # FVG - All active (for frontend visualization)
            "fvgs": {
                "bullish": [
                    {
                        "top": float(round(fvg.top, 2)),
                        "btm": float(round(fvg.btm, 2)),
                        "avg": float(round(fvg.avg, 2)),
                        "time": str(fvg.left_time) if fvg.left_time else None,
                        "mitigated": fvg.mitigated
                    }
                    for fvg in self.fvg_manager.bullish_fvgs
                ],
                "bearish": [
                    {
                        "top": float(round(fvg.top, 2)),
                        "btm": float(round(fvg.btm, 2)),
                        "avg": float(round(fvg.avg, 2)),
                        "time": str(fvg.left_time) if fvg.left_time else None,
                        "mitigated": fvg.mitigated
                    }
                    for fvg in self.fvg_manager.bearish_fvgs
                ]
            },

            # Historical data for plotting
            "timestamps": [str(t) for t in df_plot['timestamp'].tolist()],
            "close_line": [float(round(c, 2)) for c in df_plot['close'].tolist()],
            "high_line": [float(round(h, 2)) for h in df_plot['high'].tolist()],
            "low_line": [float(round(l, 2)) for l in df_plot['low'].tolist()],

            # Dashboard-specific fields (for LuxAlgo Dashboard component)
            "mtf_trends": {
                # Multi-timeframe trend data (placeholder - would need actual MTF calculation)
                # Using numeric trend values: 1 = bullish, -1 = bearish, 0 = neutral
                "1m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "3m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "5m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "10m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "15m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "30m": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "1H": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "4H": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
                "1D": {"trend": int(trend), "pattern": self.market_structure.sequence or "-"},
            },
            "detected_pattern": "None",  # Pattern detection (e.g., "Double Bottom", "Head & Shoulders")
            "recent_hhll": f"{self.market_structure.last_major} @ {round(self.market_structure.last_major_price, 2) if self.market_structure.last_major_price else 0}" if self.market_structure.last_major else "-",
            "swing_path": self.market_structure.sequence or "-",
            "zone_signal": "-",  # Zone signal status
            "zone_bias": "NEUTRAL",  # Zone bias (BULLISH/BEARISH/NEUTRAL)
            "context": "Range / No Edge",  # Market context
            "confidence": 50,  # Confidence score (0-100) - will be updated after signal generation
            "trade_mode": "WAIT",  # Trade mode (SCALP/INTRADAY/SWING/WAIT)
            "countdown": "-",  # Countdown to next signal
            "prev_trade": "-",  # Previous trade info
            "support_stack": "-",  # Support stack info
        }

        # ============================================================
        # STEP 23-24: SIGNAL GENERATION
        # ============================================================

        signal = Signal.HOLD
        strength = 50

        # Zone-based signals (highest priority)
        if accumulation_buy_signal:
            signal = Signal.BUY
            strength = 85
            reason = "Accumulation Zone Breakout + Retest"
        elif distribution_sell_signal:
            signal = Signal.SELL
            strength = 85
            reason = "Distribution Zone Breakdown + Retest"

        # Market structure signals
        elif structure_type == "BOS" and trend > 0:
            signal = Signal.BUY
            strength = 70
            reason = f"Bullish BOS | {self.market_structure.sequence}"
        elif structure_type == "BOS" and trend < 0:
            signal = Signal.SELL
            strength = 70
            reason = f"Bearish BOS | {self.market_structure.sequence}"
        elif structure_type == "CHoCH" and trend > 0:
            signal = Signal.BUY
            strength = 65
            reason = f"Bullish CHoCH | {self.market_structure.sequence}"
        elif structure_type == "CHoCH" and trend < 0:
            signal = Signal.SELL
            strength = 65
            reason = f"Bearish CHoCH | {self.market_structure.sequence}"

        # Order Block signals
        elif latest_bull_ob and not latest_bull_ob.mitigated and b.l <= latest_bull_ob.avg:
            signal = Signal.BUY
            strength = 60
            reason = "Price at Bullish OB (Demand Zone)"
        elif latest_bear_ob and not latest_bear_ob.mitigated and b.h >= latest_bear_ob.avg:
            signal = Signal.SELL
            strength = 60
            reason = "Price at Bearish OB (Supply Zone)"

        # Trend-based signals
        elif trend > 0 and self.market_structure.sequence in ["HH", "HL"]:
            signal = Signal.BUY
            strength = 55
            reason = f"Uptrend | {self.market_structure.sequence}"
        elif trend < 0 and self.market_structure.sequence in ["LL", "LH"]:
            signal = Signal.SELL
            strength = 55
            reason = f"Downtrend | {self.market_structure.sequence}"

        else:
            # Build reason with structure info
            reason_parts = []
            if structure_type:
                reason_parts.append(f"MS:{structure_type}")
            if trend != 0:
                reason_parts.append("Bullish" if trend > 0 else "Bearish")
            if self.market_structure.sequence:
                reason_parts.append(f"Seq:{self.market_structure.sequence}")

            reason = f"MTF LuxAlgo 5th - {' | '.join(reason_parts) if reason_parts else 'Building'}"

        # Update confidence in indicators with the calculated strength
        indicators["confidence"] = strength

        # Convert all numpy types to Python native types for JSON serialization
        indicators = to_python_type(indicators)

        return self.get_result(
            signal,
            strength,
            reason,
            indicators
        )

