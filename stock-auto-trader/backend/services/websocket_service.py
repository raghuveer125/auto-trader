"""
WebSocket service for real-time candle data streaming from Binance.
Connects to Binance WebSocket API and streams kline/candlestick data.
"""

import asyncio
import json
import logging
from typing import Optional, Callable
from datetime import datetime
import websockets

logger = logging.getLogger(__name__)


class BinanceWebSocketClient:
    """Client for Binance WebSocket kline/candlestick streams"""
    
    BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
    
    # Timeframe mapping: our format -> Binance format
    TIMEFRAME_MAP = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "1d": "1d",
    }
    
    def __init__(self, symbol: str, timeframe: str):
        """
        Initialize WebSocket client for a specific symbol and timeframe.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT', 'ETHUSDT')
            timeframe: Candlestick timeframe (e.g., '1m', '5m', '1h')
        """
        self.symbol = symbol.upper()
        self.timeframe = timeframe
        self.binance_timeframe = self.TIMEFRAME_MAP.get(timeframe, "1m")
        self.websocket = None
        self.running = False
        
    def _get_stream_name(self) -> str:
        """Generate Binance stream name for kline data"""
        # Binance expects lowercase symbol
        return f"{self.symbol.lower()}@kline_{self.binance_timeframe}"
    
    async def connect(self, callback: Callable):
        """
        Connect to Binance WebSocket and stream candle data.
        
        Args:
            callback: Async function to call with each candle update
        """
        stream_name = self._get_stream_name()
        url = f"{self.BINANCE_WS_URL}/{stream_name}"
        
        logger.info(f"Connecting to Binance WebSocket: {url}")
        
        self.running = True
        retry_count = 0
        max_retries = 5
        
        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(url) as websocket:
                    self.websocket = websocket
                    retry_count = 0  # Reset on successful connection
                    logger.info(f"Connected to Binance WebSocket for {self.symbol} {self.timeframe}")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(message)
                            
                            # Binance sends kline data in 'k' field
                            if 'k' in data:
                                kline = data['k']
                                
                                # Format candle data
                                candle = {
                                    'symbol': self.symbol,
                                    'timeframe': self.timeframe,
                                    'timestamp': datetime.fromtimestamp(kline['t'] / 1000).isoformat(),
                                    'open': float(kline['o']),
                                    'high': float(kline['h']),
                                    'low': float(kline['l']),
                                    'close': float(kline['c']),
                                    'volume': float(kline['v']),
                                    'is_closed': kline['x'],  # True if candle is closed
                                    'close_time': datetime.fromtimestamp(kline['T'] / 1000).isoformat(),
                                }
                                
                                # Call the callback with candle data
                                await callback(candle)
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode WebSocket message: {e}")
                        except Exception as e:
                            logger.error(f"Error processing WebSocket message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"WebSocket connection closed for {self.symbol}, reconnecting...")
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"WebSocket error for {self.symbol}: {e}")
                retry_count += 1
                await asyncio.sleep(2 ** retry_count)
                
        if retry_count >= max_retries:
            logger.error(f"Max retries reached for {self.symbol}, giving up")
            
        logger.info(f"WebSocket connection closed for {self.symbol} {self.timeframe}")
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info(f"Disconnected from Binance WebSocket for {self.symbol}")


# WebSocket connection manager
class WebSocketManager:
    """Manages multiple WebSocket connections"""
    
    def __init__(self):
        self.connections = {}  # key: (symbol, timeframe), value: BinanceWebSocketClient
        
    async def subscribe(self, symbol: str, timeframe: str, callback: Callable):
        """
        Subscribe to real-time candle updates for a symbol/timeframe.
        
        Args:
            symbol: Trading pair
            timeframe: Candlestick timeframe
            callback: Async function to call with updates
        """
        key = (symbol.upper(), timeframe)
        
        if key in self.connections:
            logger.info(f"Already subscribed to {symbol} {timeframe}")
            return
            
        client = BinanceWebSocketClient(symbol, timeframe)
        self.connections[key] = client
        
        # Start connection in background
        asyncio.create_task(client.connect(callback))
        
    async def unsubscribe(self, symbol: str, timeframe: str):
        """Unsubscribe from a symbol/timeframe stream"""
        key = (symbol.upper(), timeframe)
        
        if key in self.connections:
            client = self.connections[key]
            await client.disconnect()
            del self.connections[key]
            logger.info(f"Unsubscribed from {symbol} {timeframe}")
            
    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        for client in self.connections.values():
            await client.disconnect()
        self.connections.clear()
        logger.info("All WebSocket connections closed")


# Global WebSocket manager instance
ws_manager = WebSocketManager()
