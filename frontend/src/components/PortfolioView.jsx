import { useEffect, useState } from 'react'
import { getPortfolio, scanAndTrade } from '../api'
import { Card, Button, Stat, Spinner, Badge, cls } from './ui'

const inr = (v) => '₹' + Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })

export default function PortfolioView() {
  const [p, setP] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [actions, setActions] = useState(null)
  const [err, setErr] = useState(null)

  const load = () => { setLoading(true); getPortfolio().then(setP).catch((e) => setErr(e.message)).finally(() => setLoading(false)) }
  useEffect(load, [])

  const trade = async () => {
    setBusy(true); setActions(null)
    try { const r = await scanAndTrade(); setActions(r.actions); load() }
    catch (e) { setErr(e.message) } finally { setBusy(false) }
  }

  if (loading) return <Spinner label="Loading portfolio…" />
  if (err) return <Card className="p-4 text-rose-300 text-sm">Error: {err}</Card>

  const pnlTone = p.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'
  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-semibold">Paper portfolio</h1>
          <p className="text-sm text-slate-400">Simulated fills. The risk model sizes every position at 0.5% account risk.</p>
        </div>
        <Button tone="green" onClick={trade} disabled={busy}>{busy ? 'Scanning…' : '⚡ Scan & paper-trade'}</Button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        <Stat label="Equity" value={inr(p.equity)} />
        <Stat label="Cash" value={inr(p.cash)} />
        <Stat label="Total P&L" value={inr(p.total_pnl)} sub={`${p.total_pnl_pct}%`} tone={pnlTone} />
        <Stat label="Open positions" value={p.positions.length} />
      </div>

      {actions && (
        <Card className="p-4 mb-5">
          <div className="font-medium mb-2">Last scan placed {actions.length} paper order(s)</div>
          {actions.length === 0 && <div className="text-sm text-slate-400">No actionable long setups right now (regime/gates not met). Try again on a trending day.</div>}
          <div className="flex flex-wrap gap-2">{actions.map((a, i) => <Badge key={i} tone="green">{a.ticker.replace('.NS', '')} ×{a.shares} @ {a.entry}</Badge>)}</div>
        </Card>
      )}

      <Card className="p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
            <tr><th className="text-left p-3">Ticker</th><th className="p-3">Qty</th><th className="p-3">Avg</th><th className="p-3">Last</th><th className="p-3">Value</th><th className="p-3">P&L</th><th className="text-left p-3">Strategy</th></tr>
          </thead>
          <tbody>
            {p.positions.length === 0 && <tr><td colSpan="7" className="p-6 text-center text-slate-500">No open positions. Run a scan to populate the book.</td></tr>}
            {p.positions.map((row) => (
              <tr key={row.ticker} className="border-t border-edge">
                <td className="p-3 font-medium">{row.ticker.replace('.NS', '')}</td>
                <td className="p-3 text-center">{row.qty}</td>
                <td className="p-3 text-center">{row.avg_price}</td>
                <td className="p-3 text-center">{row.last}</td>
                <td className="p-3 text-center">{inr(row.value)}</td>
                <td className={cls('p-3 text-center font-medium', row.unrealized_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400')}>{inr(row.unrealized_pnl)} ({row.unrealized_pct}%)</td>
                <td className="p-3 text-slate-400 text-xs">{row.strategy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
