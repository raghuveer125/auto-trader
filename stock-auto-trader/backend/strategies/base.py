from enum import Enum
from typing import Dict, Optional, Any
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np


def to_python_type(obj: Any) -> Any:
    """
    Recursively convert numpy/pandas types to Python native types for JSON serialization.

    Args:
        obj: Any object that might contain numpy/pandas types

    Returns:
        Object with all numpy/pandas types converted to Python native types
    """
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: to_python_type(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_python_type(item) for item in obj]
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif pd.isna(obj):
        return None
    else:
        return obj


class Signal(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    """
    Base class for all trading strategies

    All strategies must implement:
    - name: strategy identifier
    - description: human-readable description
    - calculate(df): returns signal dict with signal, strength, reason, indicators
    """

    name: str = "BASE"
    description: str = "Base strategy class"

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate trading signal based on price data

        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume

        Returns:
            Dict with keys: strategy, signal, strength, reason, indicators
        """
        pass

    def get_result(
        self,
        signal: Signal,
        strength: int,
        reason: str,
        indicators: Optional[Dict] = None
    ) -> Dict:
        """
        Format strategy result

        Args:
            signal: Signal enum (BUY/SELL/HOLD)
            strength: Signal strength 0-100
            reason: Human-readable explanation
            indicators: Optional dict of technical indicator values

        Returns:
            Formatted result dict
        """
        # Convert strength to Python int (in case it's numpy.int64)
        strength_value = int(max(0, min(100, strength)))

        # Convert all numpy/pandas types in indicators to Python native types
        clean_indicators = to_python_type(indicators or {})

        return {
            "strategy": self.name,
            "signal": signal.value,
            "strength": strength_value,
            "reason": reason,
            "indicators": clean_indicators
        }
