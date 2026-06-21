import { useEffect, useState } from 'react'
import { getStrategies } from '../api'
import { Card, Badge, ScoreBar, Spinner } from './ui'

const readable = (v) => Array.isArray(v) ? v.join(', ') : (typeof v === 'boolean' ? (v ? 'yes' : 'no') : String(v))

export default function StrategiesView() {
  const [data, setData] = useState(null)
  const [err, setErr] = useState(null)
  useEffect(() => { getStrategies().then(setData).catch((e) => setErr(e.message)) }, [])

  if (err) return <Card className="p-4 text-rose-300 text-sm">Error: {err}</Card>
  if (!data) return <Spinner label="Loading strategies…" />

  return (
    <div>
      <h1 className="text-xl font-semibold mb-1">Strategy library</h1>
      <p className="text-sm text-slate-400 mb-4">Nine strategies — each with its fundamental and technical setup kept separate. These rules drive the signal engine.</p>
      <div className="space-y-4">
        {data.strategies.map((s) => {
          const tb = s.technical_block || {}
          const conds = tb.required_conditions || tb.sequence || []
          return (
            <Card key={s.id} className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-lg">{s.id}. {s.name}</h2>
                <div className="flex flex-wrap gap-1.5">
                  {(s.best_regimes || []).map((r) => <Badge key={r} tone="blue">{r}</Badge>)}
                  <Badge tone="slate">{s.signal_timeframe}</Badge>
                </div>
              </div>
              <div className="text-xs text-slate-400 mt-1">{s.category} · holding {s.holding_period}</div>

              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="rounded-xl bg-indigo-500/5 border border-indigo-600/20 p-4">
                  <h3 className="font-semibold text-indigo-300 mb-2">Fundamental setup</h3>
                  <p className="text-xs text-slate-400 italic mb-2">{s.fundamental_block?.purpose}</p>
                  <ul className="text-sm space-y-1">
                    {Object.entries(s.fundamental_block?.filters || {}).map(([k, v]) => (
                      <li key={k} className="flex gap-2"><span className="text-slate-400">{k.replace(/_/g, ' ')}:</span><span className="font-medium">{readable(v)}</span></li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-xl bg-emerald-500/5 border border-emerald-600/20 p-4">
                  <h3 className="font-semibold text-emerald-300 mb-2">Technical setup</h3>
                  <ul className="text-sm space-y-1 list-disc list-inside text-slate-200">
                    {conds.map((c, i) => <li key={i}>{c}</li>)}
                  </ul>
                  <div className="mt-3 space-y-1 text-sm">
                    <div><span className="text-slate-400">Entry — </span>{tb.entry_trigger}</div>
                    <div><span className="text-slate-400">Stop — </span>{tb.stop_logic}</div>
                    <div><span className="text-slate-400">Target — </span>{tb.target_logic}</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                <ScoreBar value={(s.score_weights?.fundamental || 0) * 100} label="Fund. weight" />
                <ScoreBar value={(s.score_weights?.technical || 0) * 100} label="Tech. weight" />
                <ScoreBar value={(s.score_weights?.regime || 0) * 100} label="Regime weight" />
                <div className="text-xs text-slate-400 self-end">Min R:R {tb.min_reward_to_risk || '—'} : 1</div>
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
