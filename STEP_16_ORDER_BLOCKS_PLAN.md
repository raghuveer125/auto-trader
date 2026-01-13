# Step 16: Order Blocks Implementation Plan

## 📋 Overview
Order Blocks are zones where institutional traders place large orders, creating supply (bearish) or demand (bullish) zones.

## 🎯 Key Concepts

### What is an Order Block?
- **Bullish Order Block**: Zone where price reversed upward (demand zone)
- **Bearish Order Block**: Zone where price reversed downward (supply zone)
- Created at pivot points where market structure changes
- Represents institutional buying/selling activity

### Order Block Detection Logic

#### Bullish Order Block (Demand Zone)
1. Detect internal pivot high (iH)
2. Look back from pivot to find the candle with lowest low
3. That candle is the bullish order block
4. Zone = [low, high] or [low, mid] depending on positioning

#### Bearish Order Block (Supply Zone)
1. Detect internal pivot low (iL)
2. Look back from pivot to find the candle with highest high
3. That candle is the bearish order block
4. Zone = [low, high] or [mid, high] depending on positioning

### Order Block Properties
- **top**: Upper boundary of the zone
- **btm**: Lower boundary of the zone
- **left**: Timestamp when OB was created
- **avg**: Middle line (average of top and bottom)
- **volume**: Volume of the OB candle
- **mitigated**: Whether price has returned to the zone

### Mitigation (Removal) Logic
- **Absolute**: Remove when price crosses the bottom (bull) or top (bear)
- **Middle**: Remove when price crosses the middle line

### Filtering Options
- **None**: Show all order blocks
- **BOS**: Only show OBs created on Break of Structure
- **CHoCH**: Only show OBs created on Change of Character
- **CHoCH+**: Only show OBs created on CHoCH+

### Positioning Options
- **Full**: Cover the whole candle [low, high]
- **Middle**: Cover half candle [low, mid] or [mid, high]
- **Accurate/Precise**: Adjust to body (open/close)

## 🔧 Implementation Steps

### 1. Data Structures
```python
@dataclass
class OrderBlock:
    top: float          # Upper boundary
    btm: float          # Lower boundary
    left_time: int      # Creation timestamp
    left_index: int     # Creation bar index
    avg: float          # Middle line
    volume: float       # OB candle volume
    is_bullish: bool    # True = demand, False = supply
    mitigated: bool     # Has price returned?
    structure_type: str # BOS, CHoCH, CHoCH+, or None
```

### 2. Order Block Manager
```python
class OrderBlockManager:
    def __init__(self, max_blocks=5):
        self.bullish_blocks = []
        self.bearish_blocks = []
        self.max_blocks = max_blocks
    
    def add_bullish_block(self, ob: OrderBlock)
    def add_bearish_block(self, ob: OrderBlock)
    def check_mitigation(self, current_price: float)
    def get_active_blocks(self) -> List[OrderBlock]
```

### 3. Detection Function
```python
def detect_order_block(
    df: pd.DataFrame,
    pivot_index: int,
    is_bullish: bool,
    lookback: int,
    positioning: str = "Precise"
) -> OrderBlock:
    # Find the candle that created the OB
    # Calculate zone boundaries
    # Return OrderBlock object
```

### 4. Integration with Strategy
- Detect OBs when pivots are found
- Filter based on market structure (BOS/CHoCH)
- Track mitigation
- Store last 5 active OBs
- Return OB data in indicators

## 📊 Output Format

```json
{
    "order_blocks": [
        {
            "type": "bullish",
            "top": 145.50,
            "btm": 144.20,
            "avg": 144.85,
            "volume": 1500000,
            "created_at": "2024-01-05 10:00:00",
            "mitigated": false,
            "structure": "BOS"
        },
        {
            "type": "bearish",
            "top": 148.80,
            "btm": 147.50,
            "avg": 148.15,
            "volume": 2000000,
            "created_at": "2024-01-06 14:00:00",
            "mitigated": false,
            "structure": "CHoCH"
        }
    ]
}
```

## 🎨 Visual Representation

```
Price Chart:
  
  148.80 ┌─────────────┐  Bearish OB (Supply)
  148.15 ├─────────────┤  Middle Line
  147.50 └─────────────┘
  
  ...
  
  145.50 ┌─────────────┐  Bullish OB (Demand)
  144.85 ├─────────────┤  Middle Line
  144.20 └─────────────┘
```

## 🔄 Next Steps After Implementation

1. Add OB columns to database
2. Calculate OBs in indicator service
3. Display OBs on frontend chart as boxes
4. Add OB touch alerts
5. Use OBs for signal generation

---

**Ready to implement!** This will add institutional-level zone detection to the strategy.

