import { Activity, CalendarDays, ChartNoAxesCombined, Flame, Map, ShieldAlert } from 'lucide-react'

const navigation = [
  { label: 'Overview', icon: Map },
  { label: 'Fire Calendar', icon: CalendarDays },
  { label: 'Historical Anomalies', icon: ShieldAlert },
  { label: 'Experimental Model', icon: ChartNoAxesCombined },
]

type Props = {
  activePage: string
  onNavigate: (page: string) => void
}

export function Sidebar({ activePage, onNavigate }: Props) {
  return (
    <aside className="w-full border-b border-slate-800 bg-[#0b1424] lg:min-h-screen lg:w-64 lg:border-b-0 lg:border-r">
      <div className="flex items-center gap-3 border-b border-slate-800 px-6 py-6">
        <div className="rounded-xl bg-orange-500/15 p-3 text-orange-400">
          <Flame size={25} />
        </div>
        <div>
          <h1 className="text-xl font-bold text-white">FireScope AI</h1>
          <p className="text-xs text-slate-400">Earth Observation Platform</p>
        </div>
      </div>

      <nav aria-label="Main navigation" className="grid grid-cols-2 gap-2 p-3 sm:grid-cols-4 lg:grid-cols-1 lg:p-4">
        {navigation.map(({ label, icon: Icon }) => (
          <button
            key={label}
            type="button"
            onClick={() => onNavigate(label)}
            aria-current={activePage === label ? 'page' : undefined}
            className={`flex w-full items-center gap-2 rounded-xl px-3 py-3 text-left text-xs transition-colors hover:bg-slate-800 focus-visible:outline-2 focus-visible:outline-cyan-400 sm:text-sm lg:gap-3 lg:px-4 ${
              activePage === label
                ? 'bg-orange-500/10 font-semibold text-orange-400'
                : 'text-slate-400'
            }`}
          >
            <Icon size={19} />
            <span>{label}</span>
          </button>
        ))}
      </nav>

      <div className="mx-4 mt-6 hidden rounded-xl lg:block border border-slate-700 bg-slate-800/40 p-4">
        <div className="flex items-center gap-2 text-sm font-medium text-cyan-400">
          <Activity size={17} />
          Historical Data
        </div>
        <p className="mt-2 text-xs leading-relaxed text-slate-400">
          MODIS and VIIRS satellite detections. Not individual wildfire counts.
        </p>
      </div>
    </aside>
  )
}
