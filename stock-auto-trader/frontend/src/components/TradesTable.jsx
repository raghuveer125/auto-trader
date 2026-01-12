import { Clock, DollarSign, Maximize2, Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { useState } from 'react';
import './TradesTable.css';

const TradesTable = ({ trades, strategy = null }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getPnLClass = (pnl) => {
    if (pnl > 0) return 'positive';
    if (pnl < 0) return 'negative';
    return 'neutral';
  };

  const filteredTrades = strategy
    ? trades.filter((trade) => trade.strategy === strategy)
    : trades;

  // Sort trades by timestamp (most recent first)
  const sortedTrades = [...filteredTrades].sort((a, b) => {
    const timeA = new Date(a.exit_time || a.entry_time).getTime();
    const timeB = new Date(b.exit_time || b.entry_time).getTime();
    return timeB - timeA;
  });

  if (!sortedTrades || sortedTrades.length === 0) {
    return (
      <div className="trades-table-empty">
        <Clock size={48} />
        <h3>No trades yet</h3>
        <p>
          {strategy
            ? `No trades executed for ${strategy} strategy`
            : 'No trades have been executed yet. Enable auto-trading to start.'}
        </p>
      </div>
    );
  }

  return (
    <div className={`trades-table-container ${isMinimized ? 'minimized' : ''}`}>
      <div className="trades-table-header">
        <h3>{strategy ? `${strategy} Trades` : 'All Trades'}</h3>
        <div className="trades-stats">
          <span className="trades-count">{sortedTrades.length} trades</span>
          <span className="trades-profit">
            Total P&L:{' '}
            <span
              className={getPnLClass(
                sortedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
              )}
            >
              {formatCurrency(
                sortedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0)
              )}
            </span>
          </span>
          <button
            className="trades-minimize-btn"
            onClick={() => setIsMinimized(!isMinimized)}
            title={isMinimized ? "Maximize table" : "Minimize table"}
          >
            {isMinimized ? <Maximize2 size={16} /> : <Minus size={16} />}
          </button>
        </div>
      </div>

      {!isMinimized && (
        <div className="trades-table-scroll">
          <table className="trades-table">
            <thead>
              <tr>
                <th>Date/Time</th>
                <th>Symbol</th>
                <th>Strategy</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>P&L</th>
                <th>P&L %</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sortedTrades.map((trade) => {
                // Handle both 'type' and 'trade_type' field names from API
                const tradeType = trade.type || trade.trade_type || 'BUY';
                const tradeStatus = trade.status || 'OPEN';
                const entryTime = trade.entry_time || trade.timestamp;
                const entryPrice = trade.entry_price || trade.price;

                return (
                  <tr key={trade.id} className="trade-row">
                    <td className="date-cell">{formatDate(entryTime)}</td>
                    <td className="symbol-cell">
                      <span className="symbol-badge">{trade.symbol}</span>
                    </td>
                    <td className="strategy-cell">{trade.strategy}</td>
                    <td className="type-cell">
                      <div className={`trade-type ${tradeType.toLowerCase()}`}>
                        {tradeType === 'BUY' ? (
                          <TrendingUp size={14} />
                        ) : (
                          <TrendingDown size={14} />
                        )}
                        <span>{tradeType}</span>
                      </div>
                    </td>
                    <td className="quantity-cell">{trade.quantity}</td>
                    <td className="price-cell">{formatCurrency(entryPrice)}</td>
                    <td className="price-cell">
                      {trade.exit_price ? formatCurrency(trade.exit_price) : '-'}
                    </td>
                    <td className={`pnl-cell ${getPnLClass(trade.pnl)}`}>
                      <div className="pnl-value">
                        {trade.pnl !== null && trade.pnl !== undefined ? (
                          <>
                            <DollarSign size={14} />
                            {formatCurrency(Math.abs(trade.pnl))}
                          </>
                        ) : (
                          '-'
                        )}
                      </div>
                    </td>
                    <td className={`pnl-cell ${getPnLClass(trade.pnl)}`}>
                      {trade.pnl_percent !== null && trade.pnl_percent !== undefined
                        ? `${trade.pnl_percent > 0 ? '+' : ''}${trade.pnl_percent.toFixed(2)}%`
                        : '-'}
                    </td>
                    <td className="status-cell">
                      <span className={`status-badge ${tradeStatus.toLowerCase()}`}>
                        {tradeStatus}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TradesTable;
