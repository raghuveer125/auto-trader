"""
Trading Strategy Module

Available strategies:
- MACD: Moving Average Convergence Divergence
- RSI: Relative Strength Index
- MA_CROSSOVER: Moving Average Crossover
- BOLLINGER: Bollinger Bands
- MTF_EMA: Multi-Timeframe EMA Trend
- MTF_LUXALGO_5TH: MTF LuxAlgo 5th Price Action
"""

from .base import BaseStrategy, Signal, to_python_type
from .macd import MACDStrategy
from .rsi import RSIStrategy
from .ma_crossover import MACrossoverStrategy
from .bollinger import BollingerStrategy
from .mtf_ema import MTFEMAStrategy
from .mtf_luxalgo_5th import MTFLuxAlgo5thStrategy


# Registry of all available strategies
STRATEGIES = {
    "MACD": MACDStrategy,
    "RSI": RSIStrategy,
    "MA_CROSSOVER": MACrossoverStrategy,
    "BOLLINGER": BollingerStrategy,
    "MTF_EMA": MTFEMAStrategy,
    "MTF_LUXALGO_5TH": MTFLuxAlgo5thStrategy,
}


def get_strategy(name: str) -> BaseStrategy:
    """
    Get a strategy instance by name

    Args:
        name: Strategy name (case-insensitive)

    Returns:
        Strategy instance

    Raises:
        ValueError: If strategy not found
    """
    name = name.upper()
    strategy_class = STRATEGIES.get(name)

    if not strategy_class:
        available = ", ".join(STRATEGIES.keys())
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")

    return strategy_class()


def get_all_strategies():
    """
    Get all available strategy names

    Returns:
        List of strategy names
    """
    return list(STRATEGIES.keys())


__all__ = [
    "BaseStrategy",
    "Signal",
    "to_python_type",
    "MACDStrategy",
    "RSIStrategy",
    "MACrossoverStrategy",
    "BollingerStrategy",
    "MTFEMAStrategy",
    "MTFLuxAlgo5thStrategy",
    "STRATEGIES",
    "get_strategy",
    "get_all_strategies",
]
