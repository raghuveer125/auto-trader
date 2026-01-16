# Stock Auto Trader - Setup Guide

## Prerequisites
- **Python**: 3.12+ (recommended)
- **Node.js**: 18+ and npm
- **PostgreSQL**: 15+
- **Git**: For version control

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd auto-trader/stock-auto-trader
```

### 2. Database Setup

#### Using Docker (Recommended)
```bash
docker-compose up -d
```

This creates a PostgreSQL database with:
- Database: `stock_trader`
- User: `trader`
- Password: `trader123`
- Port: `5432`

#### Manual PostgreSQL Setup
If not using Docker, create database manually:
```sql
CREATE DATABASE stock_trader;
CREATE USER trader WITH PASSWORD 'trader123';
GRANT ALL PRIVILEGES ON DATABASE stock_trader TO trader;
```

### 3. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Environment Configuration
Create a `.env` file in the `backend` directory (optional):
```env
DATABASE_URL=postgresql://trader:trader123@localhost:5432/stock_trader
```

#### Start Backend Server
```bash
python main.py
```

Backend will start on: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 4. Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Frontend will start on: `http://localhost:5173`

## Required Python Packages

The `requirements.txt` includes:
- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **sqlalchemy** - Database ORM
- **psycopg[binary]** - PostgreSQL adapter
- **python-dotenv** - Environment variables
- **pandas** - Data manipulation
- **numpy** - Numerical computing
- **yfinance** - Yahoo Finance data
- **ta** - Technical analysis indicators
- **pydantic** - Data validation
- **websockets** - WebSocket support for real-time updates
- **python-binance** - Binance API for crypto data
- **requests** - HTTP library

## Required Node Packages

The `package.json` includes:
- **react** - UI framework
- **react-dom** - React DOM renderer
- **axios** - HTTP client
- **lightweight-charts** - TradingView charts
- **lucide-react** - Icon library
- **vite** - Build tool

## Initial Data Setup

### Add Stocks
```bash
cd backend
source venv/bin/activate
python add_indian_stocks.py
```

This adds sample Indian stocks (NSE/BSE symbols).

### Sync Candle Data
Via API (after backend is running):
```bash
curl -X POST "http://localhost:8000/candles/SOLUSDT/sync?timeframe=1m&full_sync=false"
```

Or use the "Sync Data" button in the UI.

## WebSocket Support (Real-time Prices)

WebSocket connections work for **crypto symbols only** (e.g., SOLUSDT, BTCUSDT, ETHUSDT).

The backend connects to:
- **Binance WebSocket**: `wss://stream.binance.com:9443/ws`

For stock symbols (AAPL, GOOGL, etc.), prices are fetched from Yahoo Finance and stored in the database.

## Troubleshooting

### Backend won't start
1. Check if port 8000 is already in use:
   ```bash
   lsof -i :8000
   ```
2. Kill existing process:
   ```bash
   kill -9 <PID>
   ```

### Database connection error
1. Verify PostgreSQL is running:
   ```bash
   docker ps  # If using Docker
   ```
2. Check connection string in `backend/database.py`

### Frontend can't connect to API
1. Verify backend is running on port 8000
2. Check CORS settings in `backend/main.py`
3. Ensure `VITE_API_URL` is correct in `.env`

### WebSocket errors
1. Verify backend is running
2. Check browser console for connection errors
3. WebSocket only works for crypto symbols (SOLUSDT, BTCUSDT, etc.)

## Project Structure

```
stock-auto-trader/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── models.py              # Database models
│   ├── database.py            # Database connection
│   ├── requirements.txt       # Python dependencies
│   ├── services/              # Data services
│   │   ├── candle_service.py
│   │   ├── binance_service.py
│   │   └── websocket_service.py
│   └── strategies/            # Trading strategies
│       ├── macd.py
│       ├── rsi.py
│       └── mtf_luxalgo_5th.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Dashboard.jsx
│   │   ├── components/
│   │   │   ├── TradingChartWithIndicators.jsx
│   │   │   └── StrategyCard.jsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.js
│   │   └── services/
│   │       └── api.js
│   └── package.json           # Node dependencies
└── docker-compose.yml         # Database container

```

## Testing WebSocket Connection

Open `backend/test_websocket.html` in a browser to verify WebSocket connectivity:
```
file:///path/to/backend/test_websocket.html
```

## Production Deployment

### Backend
1. Set up production database
2. Update environment variables
3. Use production ASGI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Frontend
1. Build production bundle:
   ```bash
   npm run build
   ```
2. Serve `dist` folder with nginx/Apache

## Support

For issues or questions, check:
- Backend logs: `backend/logs/`
- Browser console (F12) for frontend errors
- API documentation: `http://localhost:8000/docs`
