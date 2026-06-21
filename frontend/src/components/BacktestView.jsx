import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
import { getUniverse, getStrategies, runBacktest } from '../api'
import { Card, Button, KPI, Spinner, PageHeader, Badge, cls } from './ui'

const inr = (v) => '₹' + Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })

export default function BacktestView() {
  const [tickers, setTickers] = useState([])
  const [strategies, setStrategies] = useState([])
  const [form, setForm] = useState({ ticker: 'RELIANCE.NS', strategy_id: 'S5', period: '2y', round_trip_bps: 30 })
  const [res, setRes] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState(null)

  useEffect(() => {
    getUniverse().then((u) => setTickers(u.watchlist)).catch(() => {})
    getStrategies().then((s) => setStrategies(s.strategies)).catch(() => {})
  }, [])

  const run = async () => {
    setLoading(true); setErr(null); setRes(null)
    try { setRes(await runBacktest({ ...form, round_trip_bps: Number(form.round_trip_bps) })) }
    catch (e) { setErr(e.message) } finally { setLoading(false) }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const m = res?.metrics
  const beat = m && m.total_return_pct > m.buy_hold_pct

  return (
    <div>
      <PageHeader title="Backtest" subtitle="Daily-bar simulation with realistic round-trip costs (brokerage + STT + slippage). EOD execution; stops & targets checked on later bars." />

      <Card className="p-4 mb-5">
        <div className="grid md:grid-cols-5 gap-3 items-end">
          <Field label="Ticker">
            <input list="tickers" value={form.ticker} onChange={set('ticker')} className="inp" />
            <datalist id="tickers">{tickers.map((t) => <option key={t} value={t} />)}</datalist>
          </Field>
          <Field label="Strategy">
            <select value={form.strategy_id} onChange={set('strategy_id')} className="inp">
              {strategies.map((s) => <option key={s.id} value={s.id}>{s.id} · {s.name.split(' (')[0]}</option>)}
            </select>
          </Field>
          <Field label="Period">
            <select value={form.period} onChange={set('period')} className="inp">
              {['1y', '2y', '5y'].map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </Field>
          <Field label="Round-trip cost (bps)">
            <input type="number" value={form.round_trip_bps} onChange={set('round_trip_bps')} className="inp" />
          </Field>
          <Button onClick={run} disabled={loading}>{loading ? 'Running…' : '▶ Run backtest'}</Button>
        </div>
      </Card>

      {loading && <Spinner label="Simulating…" />}
      {err && <Card className="p-4 text-rose-300 text-sm">Error: {err}</Card>}
      {res?.error && <Card className="p-4 text-amber-300 text-sm">{res.error}</Card>}

      {m && (
        <div className="space-y-5">
          {m.intraday_note && <Badge tone="amber">Intraday strategy approximated on daily bars — directional only</Badge>}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <KPI label="Strategy return" value={`${m.total_return_pct}%`} sub={`CAGR ${m.cagr_pct ?? '—'}%`} tone={m.total_return_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'} />
            <KPI label="Buy & hold" value={`${m.buy_hold_pct}%`} sub={beat ? 'strategy ahead' : 'strategy behind'} tone={beat ? 'text-emerald-400' : 'text-amber-400'} />
            <KPI label="Win rate" value={`${m.win_rate}%`} sub={`${m.trades} trades`} />
            <KPI label="Profit factor" value={m.profit_factor ?? '—'} sub={`expectancy ${m.expectancy_pct}%/trade`} />
            <KPI label="Max drawdown" value={`${m.max_drawdown_pct}%`} tone="text-rose-400" />
            <KPI label="Sharpe (proxy)" value={m.sharpe ?? '—'} />
            <KPI label="Exposure" value={`${m.exposure_pct}%`} sub="time in market" />
            <KPI label="Ending equity" value={inr(m.ending_equity)} sub={`from ${inr(m.start_cash)}`} />
          </div>

          <Card className="p-4">
            <div className="text-sm font-semibold mb-2">Equity curve — strategy vs buy &amp; hold</div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={res.equity_curve}>
                  <CartesianGrid stroke="#1f2a44" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} minTickGap={48} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 10 }} width={64} tickFormatter={(v) => '₹' + (v / 1000).toFixed(0) + 'k'} />
                  <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1f2a44', borderRadius: 12 }} formatter={(v) => inr(v)} />
                  <Legend />
                  <Line type="monotone" dataKey="strategy" stroke="#34d399" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="buy_hold" stroke="#64748b" dot={false} strokeWidth={1.5} strokeDasharray="4 3" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card className="p-0 overflow-hidden">
            <div className="px-4 py-3 text-sm font-semibold border-b border-white/10">Trades ({res.trades.length} shown)</div>
            <div className="overflow-x-auto max-h-96">
              <table className="w-full text-sm">
                <thead className="bg-white/5 text-slate-400 text-xs uppercase sticky top-0">
                  <tr><th className="text-left p-2">Entry</th><th className="text-left p-2">Exit</th><th className="p-2">In</th><th className="p-2">Out</th><th className="p-2">Bars</th><th className="p-2">Return</th><th className="text-left p-2">Reason</th></tr>
                </thead>
                <tbody>
                  {res.trades.slice().reverse().map((t, i) => (
                    <tr key={i} className="border-t border-white/5">
                      <td className="p-2">{t.entry_date}</td><td className="p-2">{t.exit_date}</td>
                      <td className="p-2 text-center">{t.entry}</td><td className="p-2 text-center">{t.exit}</td>
                      <td className="p-2 text-center text-slate-400">{t.bars}</td>
                      <td className={cls('p-2 text-center font-medium', t.ret_pct >= 0 ? 'text-emerald-400' : 'text-rose-400')}>{t.ret_pct}%</td>
                      <td className="p-2 text-slate-400">{t.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <div className="text-xs text-slate-500">Past performance does not predict future results. Validate with walk-forward and out-of-sample tests before risking capital. Not investment advice.</div>
        </div>
      )}
    </div>
  )
}

function Field({ label, children }) {
  return <label className="block"><span className="block text-xs text-slate-400 mb-1">{label}</span>{children}</label>
}
