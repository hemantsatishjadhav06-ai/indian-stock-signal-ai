import { useEffect, useState } from 'react'
import { Card, Badge, Spinner, cls } from './ui'

const BASE = import.meta.env.BASE_URL || '/'
const statusTone = { ok: 'green', warn: 'amber', fail: 'red' }
const statusIcon = { ok: '✓', warn: '!', fail: '✕' }

export default function AnalysisView() {
  const [manifest, setManifest] = useState(null)
  const [item, setItem] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    fetch(`${BASE}research/manifest.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('no manifest'))))
      .then((m) => { setManifest(m); if (m.items?.[0]) loadItem(m.items[0].file) })
      .catch(() => setManifest({ items: [] }))
  }, [])

  const loadItem = (file) => {
    setItem(null); setErr(null)
    fetch(`${BASE}research/${file}`).then((r) => r.json()).then(setItem).catch((e) => setErr(e.message))
  }

  if (!manifest) return <Spinner label="Loading research…" />

  return (
    <div>
      <h1 className="text-xl font-semibold mb-1">Research & analysis</h1>
      <p className="text-sm text-slate-400 mb-4">Hand-built deep dives, with the workbook's numbers fact-checked against primary sources. Fundamental and technical views are kept separate.</p>

      {manifest.items.length === 0 && (
        <Card className="p-6 text-slate-400 text-sm">No research notes yet. Drop JSON files into <code className="text-slate-300">frontend/public/research/</code> and list them in <code className="text-slate-300">manifest.json</code>.</Card>
      )}

      {manifest.items.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {manifest.items.map((it) => (
            <button key={it.id} onClick={() => loadItem(it.file)}
              className={cls('px-3 py-1.5 rounded-lg text-sm border', item?.id === it.id ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-panel border-edge text-slate-300 hover:border-indigo-500/50')}>
              {it.title}
            </button>
          ))}
        </div>
      )}

      {err && <Card className="p-4 text-rose-300 text-sm">Error: {err}</Card>}
      {item && (
        <div className="space-y-4">
          <Card className="p-5">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h2 className="text-2xl font-semibold">{item.title}</h2>
                <div className="text-sm text-slate-400">{item.ticker} · as of {item.as_of}</div>
              </div>
              <Badge tone={item.verdict_tone || 'slate'}>{item.verdict}</Badge>
            </div>
            <p className="text-sm text-slate-300 mt-3">{item.summary}</p>
          </Card>

          <div className="grid md:grid-cols-2 gap-4">
            <Card className="p-5">
              <h3 className="font-semibold text-indigo-300 mb-3">Fundamental</h3>
              <div className="space-y-2">
                {item.fundamental?.map((r, i) => (
                  <div key={i} className="flex justify-between gap-3 text-sm border-b border-edge/60 pb-1.5">
                    <span className="text-slate-400">{r.label}{r.note && <span className="block text-xs text-slate-500">{r.note}</span>}</span>
                    <span className="font-medium text-right">{r.value}</span>
                  </div>
                ))}
              </div>
            </Card>
            <Card className="p-5">
              <h3 className="font-semibold text-emerald-300 mb-3">Technical</h3>
              <div className="space-y-2">
                {item.technical?.map((r, i) => (
                  <div key={i} className="flex justify-between gap-3 text-sm border-b border-edge/60 pb-1.5">
                    <span className="text-slate-400">{r.label}{r.note && <span className="block text-xs text-slate-500">{r.note}</span>}</span>
                    <span className="font-medium text-right">{r.value}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          <Card className="p-5">
            <h3 className="font-semibold mb-3">Validation checks <span className="text-xs text-slate-500 font-normal">— workbook figures vs. primary sources</span></h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-slate-400 text-xs uppercase"><tr><th className="text-left p-2">Check</th><th className="text-left p-2">Workbook</th><th className="text-left p-2">Verified</th><th className="p-2">Status</th></tr></thead>
                <tbody>
                  {item.validation?.map((v, i) => (
                    <tr key={i} className="border-t border-edge align-top">
                      <td className="p-2">{v.label}{v.note && <div className="text-xs text-slate-500">{v.note}</div>}</td>
                      <td className="p-2 text-slate-300">{v.claimed}</td>
                      <td className="p-2 text-slate-300">{v.checked}</td>
                      <td className="p-2 text-center"><Badge tone={statusTone[v.status]}>{statusIcon[v.status]} {v.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {item.sources?.length > 0 && (
            <Card className="p-4">
              <div className="text-xs text-slate-400 mb-1">Sources</div>
              <ul className="text-sm space-y-1">
                {item.sources.map((s, i) => <li key={i}><a className="text-indigo-300 hover:underline" href={s.url} target="_blank" rel="noreferrer">{s.title}</a></li>)}
              </ul>
            </Card>
          )}
          <div className="text-xs text-slate-500">Educational analysis, not investment advice.</div>
        </div>
      )}
    </div>
  )
}
