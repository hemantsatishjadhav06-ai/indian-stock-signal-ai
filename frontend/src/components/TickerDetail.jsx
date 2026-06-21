import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { analyze, placeOrder } from '../api'
import { Card, Badge, Button, ScoreBar, Spinner, scoreColor, cls } from './ui'

const pct = (v) => (v == null ? '—' : (v * 100).toFixed(1) + '%')
const num = (v, d = 2) => (v == null ? '—' : Number(v).toFixed(d))
const cr = (v) => (v == null ? '—' : '₹' + (v / 1e7).toFixed(0) + ' Cr')

export default function TickerDetail({ ticker, onClose }) {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  const [msg, setMsg] = useState(null)

  useEffect(() => { analyze(ticker).then(setData).catch((e) => setErr(e.message)) }, [ticker])

  const buy = async () => {
    const best = data?.signals?.find((s) => s.bias === 'long') || data?.signals?.[0]
    try {
      const r = await placeOrder({ ticker, side: 'buy', strategy: best?.strategy || 'manual' })
      setMsg(`Paper buy filled: ${r.qty} @ ₹${r.price}`)
    } catch (e) { setMsg('Order error: ' + e.message) }
  }

  const f = data?.fundamental
  const s = data?.snapshot

  return (
    <div className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm flex items-start justify-center overflow-y-auto p-4" onClick={onClose}>
      <Card className="w-full max-w-4xl my-8 p-5" >
        <div onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold">{ticker.replace('.NS', '')}</h2>
              {data && <div className="text-sm text-slate-400">Regime: {data.regime.regime} · last ₹{num(s?.close)}</div>}
            </div>
            <Button tone="ghost" onClick={onClose}>✕ Close</Button>
          </div>

          {!data && !err && <Spinner label="Analysing…" />}
          {err && <div className="text-rose-300 text-sm mt-4">Error: {err}</div>}

          {data && (
            <>
              <div className="h-56 mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.history}>
                    <CartesianGrid stroke="#1f2a44" vertical={false} />
                    <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 10 }} minTickGap={40} />
                    <YAxis domain={['auto', 'auto']} tick={{ fill: '#64748b', fontSize: 10 }} width={48} />
                    <Tooltip contentStyle={{ background: '#121a2f', border: '1px solid #1f2a44', borderRadius: 12 }} />
                    <Line type="monotone" dataKey="close" stroke="#818cf8" dot={false} strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <Card className="p-4">
                  <div className="flex items-center justify-between mb-3"><h3 className="font-semibold text-indigo-300">Fundamental</h3>
                    <Badge tone="blue">{f?.valuation_view || 'n/a'}</Badge></div>
                  <ScoreBar value={f?.fundamental_score} label="Quality score" />
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mt-3 text-sm">
                    <Row k="Market cap" v={cr(f?.metrics?.marketCap)} />
                    <Row k="Fwd P/E" v={num(f?.metrics?.forwardPE)} />
                    <Row k="ROE" v={pct(f?.metrics?.returnOnEquity)} />
                    <Row k="Op margin" v={pct(f?.metrics?.operatingMargins)} />
                    <Row k="Rev growth" v={pct(f?.metrics?.revenueGrowth)} />
                    <Row k="D/E" v={num(f?.metrics?.debtToEquity)} />
                  </div>
                  {f?.strengths?.length > 0 && <ul className="mt-3 text-xs text-emerald-300 list-disc list-inside">{f.strengths.map((x, i) => <li key={i}>{x}</li>)}</ul>}
                  {f?.weaknesses?.length > 0 && <ul className="mt-1 text-xs text-rose-300 list-disc list-inside">{f.weaknesses.map((x, i) => <li key={i}>{x}</li>)}</ul>}
                  {!f?.data_complete && <div className="text-xs text-slate-500 mt-2">Some fundamentals missing — score treated as partial.</div>}
                </Card>

                <Card className="p-4">
                  <h3 className="font-semibold text-emerald-300 mb-3">Technical</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-sm">
                    <Row k="RSI(14)" v={num(s?.rsi14, 1)} />
                    <Row k="ADX(14)" v={num(s?.adx14, 1)} />
                    <Row k="50 DMA" v={num(s?.sma50)} />
                    <Row k="200 DMA" v={num(s?.sma200)} />
                    <Row k="ATR(14)" v={num(s?.atr14)} />
                    <Row k="MACD" v={s?.macd_bull ? 'bullish' : 'bearish'} />
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {s?.above_200dma && <Badge tone="green">above 200DMA</Badge>}
                    {s?.above_50dma && <Badge tone="green">above 50DMA</Badge>}
                    {s?.trending && <Badge tone="blue">trending</Badge>}
                  </div>
                </Card>
              </div>

              <h3 className="font-semibold mt-5 mb-2">Per-strategy signals</h3>
              <div className="overflow-x-auto rounded-xl border border-edge">
                <table className="w-full text-sm">
                  <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase">
                    <tr><th className="text-left p-2">Strategy</th><th className="p-2">Bias</th><th className="p-2">Fused</th><th className="p-2">Fund</th><th className="p-2">Tech</th><th className="p-2">Entry</th><th className="p-2">Stop</th><th className="p-2">Target</th></tr>
                  </thead>
                  <tbody>
                    {data.signals.map((sig) => (
                      <tr key={sig.strategy_id} className="border-t border-edge">
                        <td className="p-2">{sig.strategy_id}. {sig.strategy.split(' (')[0]}</td>
                        <td className="p-2 text-center">{sig.bias === 'long' ? <Badge tone="green">long</Badge> : <span className="text-slate-500">—</span>}</td>
                        <td className={cls('p-2 text-center font-medium', scoreColor(sig.fused_score))}>{sig.fused_score}</td>
                        <td className="p-2 text-center text-slate-300">{sig.fundamental_score}</td>
                        <td className="p-2 text-center text-slate-300">{sig.technical_score}</td>
                        <td className="p-2 text-center">{sig.entry ?? '—'}</td>
                        <td className="p-2 text-center text-rose-300">{sig.stop ?? '—'}</td>
                        <td className="p-2 text-center text-emerald-300">{sig.target ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-4">
                <div className="text-xs text-slate-500">Paper order auto-sizes via the 0.5%-risk model. Not investment advice.</div>
                <Button tone="green" onClick={buy}>Paper buy (best setup)</Button>
              </div>
              {msg && <div className="text-sm text-indigo-300 mt-2">{msg}</div>}
            </>
          )}
        </div>
      </Card>
    </div>
  )
}

function Row({ k, v }) {
  return <><div className="text-slate-400">{k}</div><div className="text-right font-medium">{v}</div></>
}
