# AI Copilot Instructions for Stock Auto Trader

## Project Overview
**Stock Auto Trading VR**: A paper trading (simulated) platform combining FastAPI backend with React/Vite frontend for Indian stock technical analysis. Uses multiple trading strategies (MACD, RSI, Bollinger Bands, MA Crossover) to generate BUY/SELL/HOLD signals.

## Architecture & Data Flow

### Backend Stack
- **API Framework**: FastAPI 0.115.6 (Python)
- **Database**: PostgreSQL 15 via SQLAlchemy ORM
- **Technical Indicators**: `ta` library, pandas calculations
- **Data Source**: Yahoo Finance API (stocks), Binance API (crypto)
- **Key Files**: `backend/main.py` (endpoints), `backend/models.py` (schemas), `backend/strategies/` (signal logic)

### Frontend Stack
- **Framework**: React 19 + Vite 7.2.4
- **Charts**: Lightweight Charts 4.1.3 (professional candlestick visualizations)
- **HTTP**: Axios with API abstraction layer in `frontend/src/services/api.js`
- **State**: useState for local component state (no Redux)
- **Key Files**: `frontend/src/pages/Dashboard.jsx` (main view), `frontend/src/components/` (modular UI)

### Core Data Models
1. **Stock**: Symbol tracking (BSE/NSE symbols)
2. **Candle**: OHLCV data with timeframes (1m, 5m, 15m, 30m, 1h, 2h-5h via resampling, 1d)
3. **Trade**: Executed trades with entry/exit, P&L, strategy attribution
4. **Portfolio**: Cash balance, holdings, capital tracking
5. **StrategySettings**: Configurable parameters per strategy
6. **IndicatorValue**: Pre-calculated technical indicators (stored for fast chart rendering)

### Data Flow Patterns
- **Signal Generation**: `Dashboard.jsx` → `/signals/{symbol}` endpoint → Strategy class calculates → returns {signal, strength, reason, indicators}
- **Chart Rendering**: Candles fetched → IndicatorValues retrieved → LightweightCharts renders with overlay
- **Trade Execution**: Manual or strategy-triggered → POST to `/trades/execute` → updates Portfolio & Holding records
- **Data Sync**: `POST /candles/{symbol}/sync` → fetches from Yahoo/Binance → upserts to DB → calculates indicators

## Key Conventions & Patterns

### Strategy Development
All strategies inherit from `BaseStrategy` in `backend/strategies/base.py`:
```python
class YourStrategy(BaseStrategy):
    name = "STRATEGY_NAME"
    
    def calculate(self, df: pd.DataFrame) -> Dict:
        # Must return dict from self.get_result(signal, strength, reason, indicators)
        # 'strength' is clamped to 0-100
```
- DataFrame always has: `open`, `high`, `low`, `close`, `volume`, `timestamp`
- Use `TA` library indicators when possible: `ta.momentum.rsi(df['close'], period=14)`
- Return dict with all indicator values needed for chart plotting

### API Endpoint Pattern
- CORS configured for `localhost:3000, 5173, 5174` (dev servers)
- Query params for filters, POST body for data creation
- Database session injected via `Depends(get_db)`
- Use `HTTPException(status_code=400)` for validation errors

### Frontend API Calls
- Use exported API objects from `frontend/src/services/api.js`: `stocksAPI`, `signalsAPI`, `candlesAPI`, etc.
- Never hardcode URLs—use `VITE_API_URL` env var or default `http://localhost:8000`
- Example: `const res = await signalsAPI.get(symbol, timeframe, strategy);`

### Database Relationships
- Use SQLAlchemy `relationship()` with `back_populates=` for bidirectional navigation
- Cascade deletes: `cascade="all, delete-orphan"` on parent-to-child relationships
- Unique constraints on logical composites: `(stock_id, timeframe, timestamp)` for Candles

### Enum Usage
- TimeFrame, TradeType, StrategyType defined as Python enums in models.py
- Frontend receives as strings (e.g., "BUY", "1d"), backend stores/returns as enum values

## Development Workflow

### Setup
1. Backend: `cd backend && bash setup.sh` → creates venv, installs `requirements.txt`
2. Frontend: `cd frontend && npm install`
3. Database: `docker-compose up -d` (starts PostgreSQL 15)
4. Backend run: `source backend/venv/bin/activate && python main.py` (uvicorn on port 8000)
5. Frontend run: `cd frontend && npm run dev` (Vite on port 5173)

### Common Tasks
- **Add new stock**: `POST /stocks?symbol=TCS&name=Tata%20Consultancy` (auto-syncs candles)
- **Populate test data**: `python backend/add_indian_stocks.py` (NSE/BSE symbols)
- **Sync candles**: `POST /candles/{symbol}/sync?timeframe=1d` (Yahoo Finance)
- **Fetch signals**: `GET /signals/TCS?timeframe=1d` (calculates all active strategies)

### Debugging
- Backend logs go to stdout; check `/logs/` folder for persistent logs
- Frontend: open DevTools, check Network tab for API responses
- Database: PostgreSQL runs in Docker; `docker exec stock_trader_db psql -U trader -d stock_trader` to access
- Use `/candles/{symbol}/sync-status` endpoint to verify data sync progress

### Testing
- No formal test suite—manual testing via UI or direct API calls
- Use `add_test_trades.py` to populate sample Trade data for dashboard
- Indicators API: `GET /indicators/{symbol}?timeframe=1d&limit=500` returns pre-calculated values

## Integration Points & External APIs

### Yahoo Finance
- Used for **stocks** (1m, 5m, 15m, 30m, 1h, 1d only)
- Multi-hour timeframes (2h, 3h, 4h, 5h) resampled from 1h data in `candle_service.py`
- Handles `INVALID_TIMEFRAME` if unsupported interval requested

### Binance API
- Used for **crypto symbols** (detected by `is_crypto_symbol()` in `binance_service.py`)
- Supports more flexible timeframe intervals
- Fallback for stocks if Yahoo fails

### Database Connection
- `DATABASE_URL` env var; defaults to `postgresql://trader:trader123@localhost:5432/stock_trader`
- FastAPI creates tables on startup via `Base.metadata.create_all(bind=engine)`

## Important Gotchas

1. **Timeframe Mapping**: Yahoo doesn't support 2h, 3h, 4h, 5h—must resample from 1h. Check `TIMEFRAME_MAP` and `RESAMPLE_TIMEFRAMES` in `candle_service.py`.
2. **Crypto vs Stock**: `is_crypto_symbol()` determines whether to use Binance or Yahoo. Symbols like BTC, ETH use Binance.
3. **Chart Data Limits**: Frontend requests `limit` param; store IndicatorValues up to 500+ points for smooth scrolling.
4. **Strategy Strength**: Always clamp to 0-100 in `get_result()` to avoid invalid UI ranges.
5. **CORS**: Hardcoded to localhost dev servers—production requires env-based configuration.
6. **Paper Trading Only**: No real money flows; all trades are simulated against Portfolio capital.

## File Reference Map

| Purpose | Key Files |
|---------|-----------|
| Core API | `backend/main.py` |
| Database models | `backend/models.py`, `backend/database.py` |
| Strategies | `backend/strategies/{macd,rsi,ma_crossover,bollinger,mtf_ema}.py` |
| Data fetching | `backend/services/candle_service.py`, `binance_service.py` |
| Dashboard UI | `frontend/src/pages/Dashboard.jsx` |
| Components | `frontend/src/components/{StrategyCard,SignalsTable,TradingChart}.jsx` |
| API client | `frontend/src/services/api.js` |
| Configuration | `docker-compose.yml`, `backend/requirements.txt`, `frontend/package.json` |
| Startup | `backend/setup.sh`, `re-start-services.sh` |

## Contributing New Features

1. **New Strategy**: Subclass `BaseStrategy`, implement `calculate()`, add to strategy list in `main.py`
2. **New Endpoint**: Add route in `main.py`, use `@app.get()` or `@app.post()` decorators
3. **New UI Component**: Create React component in `frontend/src/components/`, export from parent, use `stocksAPI`/`signalsAPI` imports
4. **New Database Field**: Add Column to model in `models.py`, FastAPI auto-validates via Pydantic schemas

---
*Last Updated: 2025-01-12 | Workspace: /Users/bhoomidakshpc/project1/StockAutoTradingVR/auto-trader*
