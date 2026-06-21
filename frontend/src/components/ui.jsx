export const cls = (...a) => a.filter(Boolean).join(' ')

export function scoreColor(v) {
  if (v == null) return 'text-slate-400'
  if (v >= 70) return 'text-emerald-400'
  if (v >= 55) return 'text-lime-400'
  if (v >= 45) return 'text-amber-400'
  return 'text-rose-400'
}
const dotTone = { green: 'bg-emerald-400', red: 'bg-rose-400', amber: 'bg-amber-400', blue: 'bg-indigo-400', slate: 'bg-slate-400' }

export function Card({ children, className, hover }) {
  return <div className={cls('rounded-2xl bg-slate-900/55 backdrop-blur border border-white/10 shadow-xl shadow-black/30', hover && 'card-hover', className)}>{children}</div>
}

export function Dot({ tone = 'slate', pulse }) {
  return <span className={cls('inline-block w-2 h-2 rounded-full', dotTone[tone], pulse && 'dot-pulse')} />
}

export function Badge({ children, tone = 'slate' }) {
  const tones = {
    slate: 'bg-slate-700/30 text-slate-200 border-white/10',
    green: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    red: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
    blue: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
    amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  }
  return <span className={cls('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border', tones[tone] || tones.slate)}>{children}</span>
}

export function Button({ children, onClick, tone = 'primary', disabled, className }) {
  const tones = {
    primary: 'bg-gradient-to-r from-indigo-500 to-violet-500 hover:from-indigo-400 hover:to-violet-400 text-white shadow-lg shadow-indigo-900/30',
    ghost: 'bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10',
    green: 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-white shadow-lg shadow-emerald-900/30',
  }
  return (
    <button onClick={onClick} disabled={disabled}
      className={cls('px-4 py-2 rounded-xl text-sm font-semibold transition disabled:opacity-40 disabled:cursor-not-allowed', tones[tone], className)}>
      {children}
    </button>
  )
}

export function PageHeader({ title, subtitle, right }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-slate-400 mt-0.5">{subtitle}</p>}
      </div>
      {right}
    </div>
  )
}

export function KPI({ label, value, sub, tone }) {
  return (
    <Card className="p-4">
      <div className="text-[11px] uppercase tracking-wider text-slate-400">{label}</div>
      <div className={cls('text-2xl font-bold mt-1', tone)}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </Card>
  )
}
export const Stat = KPI

export function ScoreBar({ value, label }) {
  const v = Math.max(0, Math.min(100, value || 0))
  const color = v >= 70 ? 'from-emerald-500 to-emerald-400' : v >= 55 ? 'from-lime-500 to-lime-400' : v >= 45 ? 'from-amber-500 to-amber-400' : 'from-rose-500 to-rose-400'
  return (
    <div>
      {label && <div className="flex justify-between text-xs text-slate-400 mb-1"><span>{label}</span><span className="tabular-nums">{value == null ? '—' : Math.round(value)}</span></div>}
      <div className="h-2 rounded-full bg-white/10 overflow-hidden"><div className={cls('h-full rounded-full bg-gradient-to-r', color)} style={{ width: `${v}%` }} /></div>
    </div>
  )
}

export function Spinner({ label }) {
  return (
    <div className="flex items-center gap-3 text-slate-400 text-sm py-10 justify-center">
      <span className="w-5 h-5 border-2 border-white/20 border-t-emerald-400 rounded-full animate-spin" />
      {label || 'Loading…'}
    </div>
  )
}
