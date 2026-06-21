const BASE = (import.meta.env.VITE_API_BASE || 'http://localhost:8000').replace(/\/$/, '')

async function api(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || res.statusText)
  }
  return res.json()
}

export const getUniverse = () => api('/api/universe')
export const getRegime = () => api('/api/regime')
export const getStrategies = () => api('/api/strategies')
export const getSignals = (tickers) => api('/api/signals' + (tickers ? `?tickers=${encodeURIComponent(tickers)}` : ''))
export const analyze = (ticker) => api('/api/analyze/' + encodeURIComponent(ticker))
export const getPortfolio = () => api('/api/portfolio')
export const placeOrder = (body) => api('/api/orders', { method: 'POST', body: JSON.stringify(body) })
export const scanAndTrade = () => api('/api/scan-and-trade', { method: 'POST' })
export { BASE }
export const runBacktest = (body) => api('/api/backtest', { method: 'POST', body: JSON.stringify(body) })
