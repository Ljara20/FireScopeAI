import { MapPinned, MousePointerClick } from 'lucide-react'

type Props = {
  sensor: string
  state: string
}

export function MapPanel({ sensor, state }: Props) {
  return (
    <section className="flex min-h-96 flex-col rounded-2xl border border-slate-800 bg-[#101b2d] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <MapPinned size={19} className="text-orange-400" />
            <h3 className="font-semibold text-white">
              Geographic Exploration
            </h3>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            United States · Historical satellite hotspot detections
          </p>
        </div>

        <span className="rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-300">
          {sensor.toUpperCase()}
        </span>
      </div>

      <div className="my-6 flex min-h-64 flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-[#080f1c] p-6 text-center">
        <MapPinned size={42} className="mb-4 text-slate-500" />

        <h4 className="font-semibold text-white">
          Interactive U.S. Map
        </h4>

        <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
          Geographic boundaries and state selection will be enabled
          in Phase 5.4.
        </p>

        <p className="mt-3 text-xs text-cyan-400">
          Selected geography: {state || 'All states'}
        </p>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <MousePointerClick size={15} />
        State selection will synchronize with dashboard filters.
      </div>
    </section>
  )
}
