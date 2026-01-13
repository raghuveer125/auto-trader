import { GripHorizontal } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import './LuxAlgoDashboard.css';

const LuxAlgoDashboard = ({
  indicators = {},
  draggable = false,
  initialPosition = null,
}) => {
  const [position, setPosition] = useState(initialPosition || { x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef(null);
  const startPosRef = useRef({ x: 0, y: 0 });
  const startMouseRef = useRef({ x: 0, y: 0 });

  const handleMouseDown = useCallback((e) => {
    if (!draggable) return;
    e.preventDefault();
    setIsDragging(true);
    startPosRef.current = { ...position };
    startMouseRef.current = { x: e.clientX, y: e.clientY };
  }, [draggable, position]);

  const handleMouseMove = useCallback((e) => {
    if (!isDragging) return;
    const dx = e.clientX - startMouseRef.current.x;
    const dy = e.clientY - startMouseRef.current.y;
    setPosition({
      x: startPosRef.current.x + dx,
      y: startPosRef.current.y + dy,
    });
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Debug: Log indicators when they change
  useEffect(() => {
    console.log('LuxAlgoDashboard received indicators:', indicators);
    console.log('MTF Trends:', indicators.mtf_trends);
    console.log('Market Structure:', indicators.market_structure);
    console.log('Order Blocks:', indicators.order_blocks);
  }, [indicators]);

  // Extract data from indicators
  const mtfTrends = indicators.mtf_trends || {};
  const trend = indicators.trend || 0;
  const structure = indicators.market_structure || '-';
  const sequence = indicators.pattern_sequence || '-';
  const detectedPattern = indicators.detected_pattern || 'None';
  const recentHHLL = indicators.recent_hhll || '-';
  const swingPath = indicators.swing_path || '-';
  const zoneSignal = indicators.zone_signal || '-';
  const zoneBias = indicators.zone_bias || 'NEUTRAL';
  const context = indicators.context || 'Range / No Edge';
  const confidence = indicators.confidence || 30;
  const tradeMode = indicators.trade_mode || 'WAIT';
  const countdown = indicators.countdown || '-';
  const prevTrade = indicators.prev_trade || '-';
  const supportStack = indicators.support_stack || '-';

  // Multi-timeframe data
  const timeframes = ['1m', '3m', '5m', '10m', '15m', '30m', '1H', '4H', '1D'];

  const style = draggable ? {
    transform: `translate(${position.x}px, ${position.y}px)`,
    cursor: isDragging ? 'grabbing' : 'grab',
  } : {};

  // Helper to get trend class
  const getTrendClass = (trendValue) => {
    if (trendValue === 1 || trendValue === 'BULLISH' || trendValue === 'Bullish') return 'bullish';
    if (trendValue === -1 || trendValue === 'BEARISH' || trendValue === 'Bearish') return 'bearish';
    return 'neutral';
  };

  // Helper to get trend text
  const getTrendText = (trendValue) => {
    if (trendValue === 1 || trendValue === 'BULLISH' || trendValue === 'Bullish') return 'BULLISH';
    if (trendValue === -1 || trendValue === 'BEARISH' || trendValue === 'Bearish') return 'BEARISH';
    return '-';
  };

  // Helper to get pattern icon
  const getPatternIcon = (pattern) => {
    if (pattern.includes('HH') || pattern.includes('HL')) return '↗';
    if (pattern.includes('LL') || pattern.includes('LH')) return '↘';
    return '→';
  };

  // Check if we have data
  const hasData = indicators && Object.keys(indicators).length > 0;

  if (!hasData) {
    return (
      <div className="luxalgo-dashboard">
        <div className="luxalgo-dashboard-content">
          <div className="luxalgo-section">
            <p style={{ textAlign: 'center', color: '#888', padding: '20px' }}>
              No LuxAlgo data available. Waiting for strategy calculation...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={dragRef}
      className={`luxalgo-dashboard ${draggable ? 'draggable' : ''}`}
      style={style}
      onMouseDown={handleMouseDown}
    >
      {draggable && (
        <div className="luxalgo-dashboard-drag-handle">
          <GripHorizontal size={16} />
        </div>
      )}

      <div className="luxalgo-dashboard-content">
        {/* Multi-Timeframe Trend Table */}
        <div className="luxalgo-section">
          <div className="luxalgo-mtf-table">
            <div className="luxalgo-mtf-header">
              <div className="luxalgo-mtf-cell header-cell">TF</div>
              <div className="luxalgo-mtf-cell header-cell">TREND</div>
              <div className="luxalgo-mtf-cell header-cell">PATTERN</div>
            </div>
            {timeframes.map((tf) => {
              const tfData = mtfTrends[tf] || {};
              const tfTrend = tfData.trend || 0;
              const tfPattern = tfData.pattern || '-';

              return (
                <div key={tf} className="luxalgo-mtf-row">
                  <div className="luxalgo-mtf-cell tf-label">{tf}</div>
                  <div className={`luxalgo-mtf-cell trend-cell ${getTrendClass(tfTrend)}`}>
                    {getTrendText(tfTrend)}
                  </div>
                  <div className="luxalgo-mtf-cell pattern-cell">
                    {tfPattern !== '-' && <span className="pattern-icon">{getPatternIcon(tfPattern)}</span>}
                    {tfPattern}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Pattern Detection */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Detect Pattern</span>
            <span className="luxalgo-value">{detectedPattern}</span>
          </div>
        </div>

        {/* Zone Signal & Bias */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Zone Signal</span>
            <span className={`luxalgo-value ${zoneBias === 'Zone Bias' ? 'highlight' : ''}`}>
              {zoneSignal}
            </span>
          </div>
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Zone Bias</span>
            <span className={`luxalgo-value zone-bias ${zoneBias.toLowerCase()}`}>
              {zoneBias}
            </span>
          </div>
        </div>

        {/* Recent HH/LL */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">HH / LL Age (I)</span>
            <span className="luxalgo-value">{recentHHLL}</span>
          </div>
        </div>

        {/* Swing Path */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">RECENT H/L/LL</span>
            <span className="luxalgo-value">{structure}</span>
          </div>
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">SWING PATH</span>
            <span className="luxalgo-value">{swingPath}</span>
          </div>
        </div>

        {/* Context */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Context</span>
            <span className="luxalgo-value">{context}</span>
          </div>
        </div>

        {/* Confidence Meter */}
        <div className="luxalgo-section">
          <div className="luxalgo-confidence-section">
            <div className="luxalgo-confidence-header">
              <span className="luxalgo-label">Confidence</span>
              <span className={`luxalgo-confidence-value ${confidence >= 70 ? 'high' : confidence >= 40 ? 'medium' : 'low'}`}>
                {confidence} / 100
              </span>
            </div>
            <div className="luxalgo-confidence-bar">
              <div
                className={`luxalgo-confidence-fill ${confidence >= 70 ? 'high' : confidence >= 40 ? 'medium' : 'low'}`}
                style={{ width: `${confidence}%` }}
              />
            </div>
          </div>
        </div>

        {/* Trade Info */}
        <div className="luxalgo-section">
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Countdown</span>
            <span className="luxalgo-value">{countdown}</span>
          </div>
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Trade</span>
            <span className={`luxalgo-value trade-mode ${tradeMode.toLowerCase()}`}>
              {tradeMode}
            </span>
          </div>
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Prev Trade</span>
            <span className="luxalgo-value">{prevTrade}</span>
          </div>
          <div className="luxalgo-info-row">
            <span className="luxalgo-label">Support Stack</span>
            <span className="luxalgo-value">{supportStack}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LuxAlgoDashboard;

