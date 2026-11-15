import { useEffect, useState } from 'react'
import { CalendarDays, Flame, RadioTower, Zap, type LucideIcon } from 'lucide-react'
import { getAllCalendar, type Sensor } from '../../lib/api'
import { calculateMetrics, type HistoricalMetrics } from '../../lib/metrics'

type Props = {
  sensor: Sensor
  state: string
  year: string
}

type Metric = {
  title: string
  description: string
  icon: LucideIcon
  unit: string
  value: number | null
}

const format = (value: number | null) =>
  value === null ? 'N/A' : new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 1,
  }).format(value)

export function MetricCards({ sensor, state, year }: Props) {
  const [data, setData] = useState<HistoricalMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let active = true

    getAllCalendar(sensor, state, year ? Number(year) : undefined)
      .then((records) => {
        if (!active) return
        setData(records.length ? calculateMetrics(records, state) : null)
        setError(false)
      })
      .catch(() => {
        if (!active) return
        setData(null)
        setError(true)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [sensor, state, year])

  const metrics: Metric[] = [
    {
      title: 'Satellite Detections',
      description: 'Recorded satellite hotspot detections',
      icon: Flame,
      unit: 'detections',
      value: data?.detections ?? null,
    },
    {
      title: 'Days with Detections',
      description: state
        ? 'Observed days in the selected state'
        : 'Select a state to avoid duplicate dates',
      icon: CalendarDays,
      unit: 'days',
      value: data?.daysWithDetections ?? null,
    },
    {
      title: 'Total FRP',
      description: 'Sum of valid fire radiative power values',
      icon: Zap,
      unit: 'MW',
      value: data?.frpMw ?? null,
    },
    {
      title: 'Historical Coverage',
      description: 'Years represented in the selected observations',
      icon: RadioTower,
      unit: 'years',
      value: data?.observedYears ?? null,
    },
  ]

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
        {metrics.map(({ title, description, icon: Icon, unit, value }) => (
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

            <p className="text-2xl font-bold text-white">
              {loading ? 'Loading...' : error ? 'Unavailable' : format(value)}
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
        Historical satellite observations · Not unique fires or operational risk.
      </p>
    </section>
  )
}
