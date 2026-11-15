import { BarChart3, CalendarRange } from 'lucide-react'

type Props = {
  sensor: string
  year: string
}

export function TrendsPanel({ sensor, year }: Props) {
  return (
    <section className="flex min-h-96 flex-col rounded-2xl border border-slate-800 bg-[#101b2d] p-5">
      <div className="flex items-center gap-2">
        <BarChart3 size={19} className="text-cyan-400" />
        <h3 className="font-semibold text-white">
          Historical Trends
        </h3>
      </div>

      <p className="mt-2 text-xs text-slate-400">
        Monthly satellite detection activity
      </p>

      <div className="my-6 flex min-h-64 flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-slate-700 bg-[#080f1c] p-6 text-center">
        <BarChart3 size={42} className="mb-4 text-slate-500" />

        <h4 className="font-semibold text-white">
          Awaiting Historical Data
        </h4>

        <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400">
          Sensor-specific monthly trends will be visualized
          after backend integration.
        </p>

        <p className="mt-3 text-xs text-cyan-400">
          {sensor.toUpperCase()} · {year || 'All available years'}
        </p>
      </div>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <CalendarRange size={15} />
        Historical observations only · No operational forecasts
      </div>
    </section>
  )
}
