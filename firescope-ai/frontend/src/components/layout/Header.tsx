import { Satellite } from 'lucide-react'

export function Header() {
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 px-6 py-5">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-400">
          NASA Space Apps Challenge 2026
        </p>
        <h2 className="mt-2 text-2xl font-bold text-white">
          Historical Fire Activity Dashboard
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          Explore harmonized MODIS and VIIRS hotspot detections across the United States.
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-4 py-2 text-xs text-cyan-300">
        <Satellite size={16} />
        NASA FIRMS Data
      </div>
    </header>
  )
}
