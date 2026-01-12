import { DollarSign, Package, RotateCcw, TrendingDown, TrendingUp, Wallet } from 'lucide-react';
import { Component, useCallback, useEffect, useState } from 'react';
import { portfolioAPI, tradesAPI } from '../services/api';
import './PaperTradingPanel.css';

// Error boundary to prevent crashes
class PaperTradingErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('PaperTradingPanel error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="paper-trading-error">
          <span>Paper Trading unavailable</span>
        </div>
      );
    }
    return this.props.children;
  }
}

const PaperTradingPanelInner = ({ symbol, currentPrice, strategy, onTradeExecuted }) => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [portfolio, setPortfolio] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await portfolioAPI.get();
      setPortfolio(res.data);
    } catch (err) {
      console.error('Error fetching portfolio:', err);
    }
  }, []);

  // Fetch portfolio when enabled
  useEffect(() => {
    if (isEnabled && symbol) {
      fetchPortfolio();
    }
  }, [isEnabled, symbol, fetchPortfolio]);

  const handleTrade = async (tradeType) => {
    if (!currentPrice || !symbol || quantity <= 0) return;

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await tradesAPI.execute(
        symbol,
        tradeType,
        quantity,
        currentPrice,
        strategy || 'MANUAL'
      );

      const priceStr = typeof currentPrice === 'number' ? currentPrice.toFixed(2) : currentPrice;
      setSuccess(`${tradeType} ${quantity} ${symbol} @ $${priceStr}`);

      // Refresh portfolio locally
      await fetchPortfolio();

      // Notify parent to refresh portfolio
      if (onTradeExecuted) {
        await onTradeExecuted(res.data);
      }

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Trade failed');
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset portfolio to $10,000? This will clear all trades and holdings.')) {
      return;
    }

    setLoading(true);
    try {
      await portfolioAPI.reset();
      await fetchPortfolio();
      setSuccess('Portfolio reset to $10,000');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError('Failed to reset portfolio');
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Don't render if no symbol
  if (!symbol) {
    return null;
  }

  // Calculate values safely
  const safeCurrentPrice = typeof currentPrice === 'number' && !isNaN(currentPrice) ? currentPrice : 0;
  const safeQuantity = typeof quantity === 'number' && !isNaN(quantity) ? quantity : 0;
  const totalValue = safeQuantity * safeCurrentPrice;

  // Find holding for current symbol
  const currentHolding = portfolio?.holdings?.find(h => h.symbol === symbol);

  if (!isEnabled) {
    return (
      <button
        className="paper-trading-toggle"
        onClick={() => setIsEnabled(true)}
      >
        <Wallet size={16} />
        Paper Trading
      </button>
    );
  }

  return (
    <div className="paper-trading-panel">
      <div className="paper-trading-header">
        <div className="paper-trading-title">
          <Wallet size={18} />
          <span>Paper Trading</span>
        </div>
        <button
          className="paper-trading-close"
          onClick={() => setIsEnabled(false)}
        >
          &times;
        </button>
      </div>

      {/* Portfolio Summary */}
      <div className="portfolio-summary">
        <div className="portfolio-item">
          <DollarSign size={14} />
          <span className="portfolio-label">Cash:</span>
          <span className="portfolio-value">
            ${portfolio?.cash_balance != null ? portfolio.cash_balance.toFixed(2) : '0.00'}
          </span>
        </div>
        {currentHolding && currentHolding.quantity > 0 && (
          <div className="portfolio-item">
            <Package size={14} />
            <span className="portfolio-label">{symbol}:</span>
            <span className="portfolio-value">
              {currentHolding.quantity} @ ${currentHolding.avg_buy_price != null ? currentHolding.avg_buy_price.toFixed(2) : '0.00'}
            </span>
          </div>
        )}
        <div className="portfolio-item pnl">
          <span className="portfolio-label">P&L:</span>
          <span className={`portfolio-value ${(portfolio?.pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
            {(portfolio?.pnl || 0) >= 0 ? '+' : ''}${portfolio?.pnl != null ? portfolio.pnl.toFixed(2) : '0.00'}
            ({portfolio?.pnl_percent != null ? portfolio.pnl_percent.toFixed(1) : '0'}%)
          </span>
        </div>
      </div>

      {/* Trade Form */}
      <div className="trade-form">
        <div className="trade-input-row">
          <label>Qty:</label>
          <input
            type="number"
            min="0.001"
            step="0.001"
            value={quantity}
            onChange={(e) => setQuantity(parseFloat(e.target.value) || 0)}
            disabled={loading}
          />
          <span className="trade-total">
            = ${totalValue.toFixed(2)}
          </span>
        </div>

        <div className="trade-buttons">
          <button
            className="trade-btn buy"
            onClick={() => handleTrade('BUY')}
            disabled={loading || !safeCurrentPrice || safeQuantity <= 0 || totalValue > (portfolio?.cash_balance || 0)}
          >
            <TrendingUp size={16} />
            BUY
          </button>
          <button
            className="trade-btn sell"
            onClick={() => handleTrade('SELL')}
            disabled={loading || !safeCurrentPrice || safeQuantity <= 0 || safeQuantity > (currentHolding?.quantity || 0)}
          >
            <TrendingDown size={16} />
            SELL
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && <div className="trade-message error">{error}</div>}
      {success && <div className="trade-message success">{success}</div>}

      {/* Reset Button */}
      <button
        className="reset-btn"
        onClick={handleReset}
        disabled={loading}
      >
        <RotateCcw size={14} />
        Reset Capital
      </button>
    </div>
  );
};

// Wrapper with error boundary
const PaperTradingPanel = (props) => (
  <PaperTradingErrorBoundary>
    <PaperTradingPanelInner {...props} />
  </PaperTradingErrorBoundary>
);

export default PaperTradingPanel;
