/**
 * Utility function to get currency symbol based on stock symbol
 * Indian stocks (.NS, .BO) use ₹, others use $
 */
export function getCurrencySymbol(symbol) {
  if (!symbol) return '$'
  const upperSymbol = symbol.toUpperCase()
  // Indian stocks have .NS (NSE) or .BO (BSE) suffix
  if (upperSymbol.endsWith('.NS') || upperSymbol.endsWith('.BO')) {
    return '₹'
  }
  return '$'
}

/**
 * Format price with appropriate currency symbol
 */
export function formatPrice(price, symbol) {
  if (price === null || price === undefined) return '—'
  const currencySymbol = getCurrencySymbol(symbol)
  return `${currencySymbol}${Number(price).toFixed(2)}`
}
