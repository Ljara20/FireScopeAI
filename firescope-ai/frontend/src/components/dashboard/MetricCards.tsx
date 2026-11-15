import {
  CalendarDays,
  Flame,
  RadioTower,
  Zap,
  type LucideIcon,
} from 'lucide-react'

type Metric = {
  title: string
  description: string
  icon: LucideIcon
  unit: string
}

const metrics: Metric[] = [
  {
    title: 'Satellite Detections',
    description: 'Recorded satellite hotspot detections',
    icon: Flame,
    unit: 'detections',
  },
  {
    title: 'Days with Detections',
    description: 'Days with observed satellite activity',
    icon: CalendarDays,
    unit: 'days',
  },
  {
    title: 'Total FRP',
    description: 'Sum of valid fire radiative power values',
    icon: Zap,
    unit: 'MW',
  },
  {
    title: 'Historical Coverage',
    description: 'Available historical observation period',
    icon: RadioTower,
    unit: 'years',
  },
]

export function MetricCards() {
  return (
    <section aria-label="Historical activity indicators">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">
          Satellite Detection Overview
        </h3>
        <p className="mt-1 text-sm text-slate-400">
          Historical indicators for the selected sensor, state and period.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ title, description, icon: Icon, unit }) => (
          <article
            key={title}
            className="rounded-2xl border border-slate-800 bg-[#101b2d] p-5"
          >
            <div className="mb-5 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-300">
                {title}
              </span>

              <span className="rounded-xl bg-orange-500/10 p-2.5 text-orange-400">
                <Icon size={20} />
              </span>
            </div>

            <p className="text-2xl font-bold text-slate-400">
              Awaiting data
            </p>

            <p className="mt-1 text-xs text-cyan-400">
              Unit: {unit}
            </p>

            <p className="mt-4 text-xs leading-relaxed text-slate-500">
              {description}
            </p>
          </article>
        ))}
      </div>

      <p className="mt-3 text-xs text-amber-300">
        Preview only · Real historical values will be loaded from FastAPI.
      </p>
    </section>
  )
}
