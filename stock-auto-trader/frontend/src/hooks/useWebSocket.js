import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Custom hook for WebSocket connection to receive real-time candle updates
 * 
 * @param {string} symbol - Trading symbol (e.g., 'BTCUSDT')
 * @param {string} timeframe - Timeframe (e.g., '1m', '5m', '1h')
 * @param {function} onUpdate - Callback function when new candle data arrives
 * @param {boolean} enabled - Whether WebSocket should be connected
 * @param {function} onCandleSaved - Callback function when a candle is saved to database
 */
export const useWebSocket = (symbol, timeframe, onUpdate, enabled = true, onCandleSaved = null) => {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const onUpdateRef = useRef(onUpdate);
  const onCandleSavedRef = useRef(onCandleSaved);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Keep onUpdate ref current
  useEffect(() => {
    onUpdateRef.current = onUpdate;
    onCandleSavedRef.current = onCandleSaved;
  }, [onUpdate, onCandleSaved]);

  const connect = useCallback(() => {
    if (!enabled || !symbol || !timeframe) {
      return;
    }

    // Close existing connection if it exists
    if (wsRef.current) {
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        console.log(`⚠️ WebSocket already connecting/connected for ${symbol} ${timeframe}, skipping`);
        return;
      }
      wsRef.current.close();
    }

    try {
      const wsUrl = `ws://localhost:8000/ws/${symbol}/${timeframe}`;
      console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`✅ WebSocket connected for ${symbol} ${timeframe}`);
        setIsConnected(true);
        setError(null);

        // Start ping interval to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 25000);

        ws.pingInterval = pingInterval;
      };

      ws.onmessage = (event) => {
        try {
          // Handle plain text messages (ping/pong)
          if (typeof event.data === 'string' && (event.data === 'ping' || event.data === 'pong')) {
            if (event.data === 'ping') {
              ws.send('pong');
            }
            return;
          }

          // Parse JSON data
          const data = JSON.parse(event.data);

          // Handle ping/pong JSON format
          if (data.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
            return;
          }

          // Handle candle saved notification
          if (data.type === 'candle_saved') {
            console.log('💾 Candle saved to database, refreshing chart...');
            if (onCandleSavedRef.current) {
              onCandleSavedRef.current();
            }
            return;
          }

          // Handle candle update
          if (data.timestamp && data.open !== undefined) {
            console.log(`📊 Candle update: ${symbol} ${timeframe}`, {
              close: data.close,
              is_closed: data.is_closed,
              time: data.timestamp
            });
            onUpdateRef.current(data);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err, event.data);
        }
      };

      ws.onerror = (err) => {
        console.error(`❌ WebSocket error for ${symbol}:`, err);
        console.error(`WebSocket URL: ws://localhost:8000/ws/${symbol}/${timeframe}`);
        console.error(`WebSocket readyState: ${ws.readyState}`);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log(`🔌 WebSocket disconnected for ${symbol} ${timeframe}`);
        setIsConnected(false);

        // Clear ping interval
        if (ws.pingInterval) {
          clearInterval(ws.pingInterval);
        }

        // Don't auto-reconnect - let component remount handle it
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [symbol, timeframe, enabled]); // Removed onUpdate from dependencies

  // Connect on mount and when dependencies change
  useEffect(() => {
    if (!enabled || !symbol || !timeframe) {
      return;
    }

    connect();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        // Clear ping interval
        if (wsRef.current.pingInterval) {
          clearInterval(wsRef.current.pingInterval);
        }
        wsRef.current.close();
        wsRef.current = null;
      }

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  // Disconnect method
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    setIsConnected(false);
  }, []);

  return {
    isConnected,
    error,
    disconnect
  };
};
