import { useEffect, useState } from 'react'
import { getRegime } from './api'
import { Dot, cls } from './components/ui'
import SignalsView from './components/SignalsView'
import PortfolioView from './components/PortfolioView'
import StrategiesView from './components/StrategiesView'
import AnalysisView from './components/AnalysisView'
import BacktestView from './components/BacktestView'

const TABS = [
  { id: 'signals', label: 'Signals' },
  { id: 'portfolio', label: 'Paper Portfolio' },
  { id: 'strategies', label: 'Strategies' },
  { id: 'backtest', label: 'Backtest' },
  { id: 'analysis', label: 'Research' },
]
const regimeTone = (r) => ({ bullish: 'green', bearish: 'red', range: 'amber', volatile: 'red', event_risk: 'amber' }[r] || 'slate')

export default function App() {
  const [tab, setTab] = useState('signals')
  const [regime, setRegime] = useState(null)
  useEffect(() => { getRegime().then(setRegime).catch(() => {}) }, [])

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/70 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-400 grid place-items-center font-extrabold text-slate-900 shadow-lg shadow-emerald-900/40">₹</div>
            <div>
              <div className="font-bold leading-tight text-[15px]"><span className="grad-text">Indian Stock AI</span></div>
              <div className="text-[11px] text-slate-400 leading-tight">Signals · Fundamental + Technical · Paper trading</div>
            </div>
          </div>
          {regime && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-white/5 text-xs">
              <Dot tone={regimeTone(regime.regime)} pulse />
              <span className="text-slate-300">Regime</span>
              <span className="font-semibold capitalize">{regime.regime}</span>
              <span className="text-slate-500">· {regime.confidence}%</span>
            </div>
          )}
        </div>
        <nav className="max-w-7xl mx-auto px-5 pb-3 flex gap-1.5">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={cls('px-4 py-2 rounded-xl text-sm font-medium transition',
                tab === t.id ? 'bg-white/10 text-white ring-1 ring-white/15' : 'text-slate-400 hover:text-slate-200 hover:bg-white/5')}>
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-5 py-7">
        {tab === 'signals' && <SignalsView />}
        {tab === 'portfolio' && <PortfolioView />}
        {tab === 'strategies' && <StrategiesView />}
        {tab === 'backtest' && <BacktestView />}
        {tab === 'analysis' && <AnalysisView />}
      </main>

      <footer className="max-w-7xl mx-auto px-5 py-10 text-xs text-slate-500 border-t border-white/5 mt-6">
        Educational tool. Signals come from deterministic rules + scoring, not investment advice. Paper trading only by default.
      </footer>
    </div>
  )
}
