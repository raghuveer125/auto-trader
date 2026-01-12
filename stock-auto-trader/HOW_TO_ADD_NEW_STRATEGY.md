# How to Add a New Trading Strategy

This guide explains all the places you need to update to add a new trading strategy to the system.

## Overview

Adding a new strategy requires changes in both **backend** (Python) and **frontend** (React). The system is designed to be modular, so most changes follow a consistent pattern.

---

## Backend Changes (Python)

### 1. Create Strategy Class

**Location:** `stock-auto-trader/backend/strategies/your_strategy.py`

Create a new file that extends `BaseStrategy`:

```python
import pandas as pd
from typing import Dict
from .base import BaseStrategy, Signal


class YourStrategy(BaseStrategy):
    """
    Your Strategy Description
    
    BUY: When condition X happens
    SELL: When condition Y happens
    """
    
    name = "YOUR_STRATEGY"  # Must be uppercase, use underscores
    description = "Brief description of your strategy"
    
    def __init__(self, param1: int = 14, param2: float = 2.0):
        """Initialize with configurable parameters"""
        self.param1 = param1
        self.param2 = param2
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        """
        Calculate trading signal based on price data
        
        Args:
            df: DataFrame with columns: timestamp, open, high, low, close, volume
            
        Returns:
            Dict with keys: strategy, signal, strength, reason, indicators
        """
        # Check if enough data
        if len(df) < self.param1:
            return self.get_result(Signal.HOLD, 0, "Insufficient data")
        
        # Calculate your indicators
        # Example: indicator = df['close'].rolling(window=self.param1).mean()
        
        # Determine signal
        # if buy_condition:
        #     return self.get_result(Signal.BUY, strength, reason, indicators)
        # elif sell_condition:
        #     return self.get_result(Signal.SELL, strength, reason, indicators)
        # else:
        #     return self.get_result(Signal.HOLD, 50, reason, indicators)
        
        # Build indicators dict for frontend display
        indicators = {
            "indicator1": value1,
            "indicator2": value2,
            # Add indicator lines for chart (optional)
            "indicator1_line": indicator_series.tolist(),  # For line charts
        }
        
        return self.get_result(Signal.BUY, 75, "Your reason", indicators)
```

**Key Points:**
- Extend `BaseStrategy`
- Set `name` (uppercase) and `description`
- Implement `calculate(df)` method
- Return indicators dict for frontend display
- Use `self.get_result()` helper method

---

### 2. Register Strategy

**Location:** `stock-auto-trader/backend/strategies/__init__.py`

Add your strategy to the imports and registry:

```python
from .your_strategy import YourStrategy

STRATEGIES = {
    "MACD": MACDStrategy,
    "RSI": RSIStrategy,
    "MA_CROSSOVER": MACrossoverStrategy,
    "BOLLINGER": BollingerStrategy,
    "MTF_EMA": MTFEMAStrategy,
    "YOUR_STRATEGY": YourStrategy,  # Add this line
}
```

---

### 3. Add to StrategyType Enum

**Location:** `stock-auto-trader/backend/models.py`

Add your strategy to the enum (around line 34):

```python
class StrategyType(enum.Enum):
    MACD = "MACD"
    RSI = "RSI"
    MA_CROSSOVER = "MA_CROSSOVER"
    BOLLINGER = "BOLLINGER"
    MTF_EMA = "MTF_EMA"
    YOUR_STRATEGY = "YOUR_STRATEGY"  # Add this line
    MANUAL = "MANUAL"
```

---

### 4. Add Strategy Settings (Optional)

If your strategy has configurable parameters:

**Location:** `stock-auto-trader/backend/models.py` (StrategySettings class, around line 177)

Add columns for your strategy's parameters:

```python
class StrategySettings(Base):
    # ... existing fields ...
    
    # Your strategy settings
    your_param1 = Column(Integer, default=14)
    your_param2 = Column(Float, default=2.0)
```

---

### 5. Add Settings Handler

**Location:** `stock-auto-trader/backend/main.py`

In the `_get_strategy_with_settings` function (around line 517), add your strategy:

```python
def _get_strategy_with_settings(strategy_name: str, db: Session):
    # ... existing code ...
    
    if setting:
        # ... existing strategies ...
        elif strategy_name.upper() == "YOUR_STRATEGY":
            return strategy_class(
                param1=setting.your_param1,
                param2=setting.your_param2
            )
```

In `_format_strategy_settings` function (around line 1125):

```python
def _format_strategy_settings(setting, strategy_type):
    # ... existing code ...
    elif strategy_type == StrategyType.YOUR_STRATEGY:
        return {
            "param1": setting.your_param1,
            "param2": setting.your_param2,
        }
```

In `_get_default_settings` function (around line 1155):

```python
def _get_default_settings(strategy_type):
    # ... existing code ...
    elif strategy_type == StrategyType.YOUR_STRATEGY:
        return {"param1": 14, "param2": 2.0}
```

---

## Frontend Changes (React)

### 6. Add Strategy Icon (Optional)

**Location:** `stock-auto-trader/frontend/src/components/StrategyCard.jsx`

In the `getStrategyIcon` function (around line 100):

```javascript
const getStrategyIcon = (strategy) => {
  switch (strategy) {
    // ... existing cases ...
    case 'YOUR_STRATEGY':
      return <YourIcon size={20} />;  // Import icon from lucide-react
    default:
      return <TrendingUp size={20} />;
  }
};
```

---

### 7. Add Strategy Settings UI (Optional)

**Location:** `stock-auto-trader/frontend/src/components/StrategySettingsModal.jsx`

Add default settings (around line 10):

```javascript
const strategyDefaults = {
  // ... existing strategies ...
  YOUR_STRATEGY: {
    param1: { label: 'Parameter 1', value: 14, min: 1, max: 100, step: 1 },
    param2: { label: 'Parameter 2', value: 2.0, min: 0.1, max: 5.0, step: 0.1 },
  },
};
```

---

## That's It!

After making these changes:

1. **Restart the backend** to load the new strategy
2. **Refresh the frontend** to see the new strategy checkbox
3. **Sync data** for a stock to calculate indicators
4. **Check the strategy card** appears in the dashboard

---

## Summary Checklist

### Backend (7 files):
- [ ] Create strategy class: `strategies/your_strategy.py`
- [ ] Register in: `strategies/__init__.py`
- [ ] Add enum: `models.py` → `StrategyType`
- [ ] Add settings columns: `models.py` → `StrategySettings` (optional)
- [ ] Add settings handler: `main.py` → `_get_strategy_with_settings` (optional)
- [ ] Add format handler: `main.py` → `_format_strategy_settings` (optional)
- [ ] Add defaults: `main.py` → `_get_default_settings` (optional)

### Frontend (2 files):
- [ ] Add icon: `StrategyCard.jsx` → `getStrategyIcon` (optional)
- [ ] Add settings UI: `StrategySettingsModal.jsx` → `strategyDefaults` (optional)

---

## Example: See Existing Strategies

For reference, check these existing strategies:
- **Simple:** `strategies/rsi.py` - Basic indicator with thresholds
- **Crossover:** `strategies/macd.py` - Line crossover detection
- **Bands:** `strategies/bollinger.py` - Price bands strategy
- **Complex:** `strategies/mtf_ema.py` - Multi-timeframe analysis

Good luck building your strategy! 🚀

