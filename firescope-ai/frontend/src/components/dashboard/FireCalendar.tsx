import { useState } from 'react'
import { CalendarDays, Flame } from 'lucide-react'
import { useHistoricalData } from '../../hooks/useHistoricalData'
import type { Sensor } from '../../lib/api'

type Props = {
  sensor: Sensor
  state: string
  year: string
}

const months = [
  'January', 'February', 'March', 'April',
  'May', 'June', 'July', 'August',
  'September', 'October', 'November', 'December',
]

const format = (value: number) =>
  new Intl.NumberFormat('en-US').format(value)

export function FireCalendar({ sensor, state, year }: Props) {
  const [selectedMonth, setSelectedMonth] = useState(1)
  const query = useHistoricalData(sensor, year)

  const loading = query.isPending || query.isFetching
  const error = query.isError

  const records = !loading && !error
    ? query.data.filter(
        (record) => !state || record.state_code === state,
      )
    : []

  const monthly = months.map((name, index) => {
    const matching = records.filter(
      (record) => record.month === index + 1,
    )

    return {
      month: index + 1,
      name,
      detections: matching.reduce(
        (sum, record) => sum + record.detection_count, 0,
      ),
      frp: matching.reduce(
        (sum, record) => sum + (record.frp_sum_mw ?? 0), 0,
      ),
      years: new Set(matching.map((record) => record.year)).size,
    }
  })

  const maximum = Math.max(0, ...monthly.map((item) => item.detections))
  const selected = monthly[selectedMonth - 1]

  function color(value: number) {
    if (value === 0 || maximum === 0) return '#263449'

    const intensity = Math.log1p(value) / Math.log1p(maximum)

    if (intensity > 0.8) return '#f97316'
    if (intensity > 0.6) return '#ea580c'
    if (intensity > 0.4) return '#c2410c'
    if (intensity > 0.2) return '#7c2d12'
    return '#43302c'
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#101b2d] p-6">
      <div className="mb-2 flex items-center gap-2">
        <CalendarDays className="text-orange-400" size={22} />
        <h2 className="text-xl font-bold text-white">Fire Calendar</h2>
      </div>

      <p className="mb-5 text-sm text-slate-400">
        Explore historical satellite detections by month.
      </p>

      <p className="mb-5 text-xs text-cyan-400">
        {sensor.toUpperCase().replaceAll('_', ' ')}
        {' · '}
        {state || 'All states'}
        {' · '}
        {year || 'All available years'}
      </p>

      {loading ? (
        <p className="py-12 text-center text-slate-400">
          Loading historical observations...
        </p>
      ) : error ? (
        <p className="py-12 text-center text-red-400">
          Unable to load historical observations.
        </p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {monthly.map((item) => (
              <button
                key={item.month}
                type="button"
                onClick={() => setSelectedMonth(item.month)}
                aria-pressed={selectedMonth === item.month}
                className={
                  'rounded-xl border p-4 text-left transition hover:border-cyan-400 ' +
                  (selectedMonth === item.month
                    ? 'border-cyan-400'
                    : 'border-slate-700')
                }
                style={{ backgroundColor: color(item.detections) }}
              >
                <span className="text-sm font-semibold text-white">
                  {item.name}
                </span>
                <p className="mt-3 text-xl font-bold text-white">
                  {format(item.detections)}
                </p>
                <span className="text-xs text-slate-200">
                  detections
                </span>
              </button>
            ))}
          </div>

          <div className="mt-6 rounded-xl border border-slate-700 bg-[#080f1c] p-5">
            <div className="mb-3 flex items-center gap-2">
              <Flame size={19} className="text-orange-400" />
              <h3 className="font-semibold text-white">
                {selected.name} · Historical Summary
              </h3>
            </div>

            <div className="grid gap-4 text-sm sm:grid-cols-3">
              <div>
                <p className="text-slate-400">Detections</p>
                <p className="mt-1 text-xl font-bold text-white">
                  {format(selected.detections)}
                </p>
              </div>

              <div>
                <p className="text-slate-400">Total valid FRP</p>
                <p className="mt-1 text-xl font-bold text-white">
                  {format(Math.round(selected.frp))} MW
                </p>
              </div>

              <div>
                <p className="text-slate-400">Years represented</p>
                <p className="mt-1 text-xl font-bold text-white">
                  {selected.years}
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      <p className="mt-5 text-xs text-slate-500">
        Historical NASA FIRMS observations only. Counts are satellite
        detections, not unique wildfires or operational risk.
        When all years are selected, monthly values are summed across years.
      </p>
    </section>
  )
}
