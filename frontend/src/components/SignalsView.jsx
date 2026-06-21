import { useEffect, useState } from 'react'
import { getSignals } from '../api'
import { Card, Badge, Button, KPI, ScoreBar, Spinner, PageHeader, Dot, cls } from './ui'
import TickerDetail from './TickerDetail'

const regimeTone = (r) => ({ bullish: 'green', bearish: 'red', range: 'amber', volatile: 'red' }[r] || 'slate')

export default function SignalsView() {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [selected, setSelected] = useState(null)

  const load = () => { setLoading(true); setError(null); getSignals().then(setData).catch((e) => setError(e.message)).finally(() => setLoading(false)) }
  useEffect(load, [])

  const results = data?.results || []
  const actionable = results.filter((r) => r.best && r.best.bias === 'long')
  const top = results[0]

  return (
    <div>
      <PageHeader
        title="Live signals"
        subtitle="Every watchlist name scored by all 9 strategies. Click a card for the full fundamental + technical breakdown."
        right={<Button onClick={load} tone="ghost">↻ Rescan</Button>}
      />

      {!loading && data && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KPI label="Market regime" value={<span className="capitalize flex items-center gap-2"><Dot tone={regimeTone(data.regime.regime)} pulse />{data.regime.regime}</span>} sub={`${data.regime.confidence}% confidence`} />
          <KPI label="Actionable setups" value={actionable.length} sub={`of ${results.length} scanned`} tone={actionable.length ? 'text-emerald-400' : undefined} />
          <KPI label="Universe" value={results.length} sub="watchlist size" />
          <KPI label="Top pick" value={top ? top.ticker.replace('.NS', '') : '—'} sub={top?.best ? `score ${top.best.fused_score}` : ''} />
        </div>
      )}

      {loading && <Spinner label="Scanning watchlist…" />}
      {error && <Card className="p-4 text-rose-300 text-sm">Error: {error}. Is the backend running and VITE_API_BASE set?</Card>}

      {!loading && data && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {results.map((r) => {
            const best = r.best
            const isLong = best && best.bias === 'long'
            return (
              <Card key={r.ticker} hover className="p-4 cursor-pointer hover:border-emerald-400/40" >
                <div onClick={() => setSelected(r.ticker)}>
                  <div className="flex items-center justify-between">
                    <div className="font-bold text-lg">{r.ticker.replace('.NS', '')}</div>
                    {best ? <Badge tone={isLong ? 'green' : 'slate'}>{isLong ? '● LONG setup' : 'No trade'}</Badge> : <Badge tone="red">{r.error ? 'error' : 'n/a'}</Badge>}
                  </div>
                  {best && (
                    <>
                      <div className="text-xs text-slate-400 mt-1 truncate">{best.strategy}</div>
                      <div className="mt-3"><ScoreBar value={best.fused_score} label="Fused score" /></div>
                      <div className="grid grid-cols-2 gap-3 mt-2">
                        <ScoreBar value={best.fundamental_score} label="Fundamental" />
                        <ScoreBar value={best.technical_score} label="Technical" />
                      </div>
                      {isLong && (
                        <div className="grid grid-cols-3 gap-2 mt-3 text-center text-xs">
                          <div className="rounded-lg bg-white/5 py-1.5"><div className="text-slate-400">Entry</div><div className="font-semibold">{best.entry}</div></div>
                          <div className="rounded-lg bg-white/5 py-1.5"><div className="text-slate-400">Stop</div><div className="font-semibold text-rose-300">{best.stop}</div></div>
                          <div className="rounded-lg bg-white/5 py-1.5"><div className="text-slate-400">Target</div><div className="font-semibold text-emerald-300">{best.target}</div></div>
                        </div>
                      )}
                      <div className="text-xs text-slate-500 mt-3">{r.actionable_count} of 9 strategies actionable</div>
                    </>
                  )}
                  {r.error && <div className="text-xs text-rose-300 mt-2">{r.error}</div>}
                </div>
              </Card>
            )
          })}
        </div>
      )}

      {selected && <TickerDetail ticker={selected} onClose={() => setSelected(null)} />}
    </div>
  )
}
