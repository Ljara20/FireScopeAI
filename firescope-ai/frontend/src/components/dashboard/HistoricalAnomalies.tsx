import { ShieldAlert } from 'lucide-react'
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
  new Intl.NumberFormat('en-US').format(Math.round(value))

export function HistoricalAnomalies({ sensor, state, year }: Props) {
  // Load the complete historical series for a valid baseline.
  const query = useHistoricalData(sensor, '')
  const loading = query.isPending || query.isFetching
  const error = query.isError

  const records = !loading && !error
    ? query.data.filter(
        (record) => !state || record.state_code === state,
      )
    : []

  const availableYears = [...new Set(records.map((record) => record.year))]
    .sort((a, b) => b - a)

  const selectedYear = year ? Number(year) : availableYears[0]

  const results = months.map((month, index) => {
    const monthNumber = index + 1

    const annual = new Map<number, number>()

    for (const record of records) {
      if (record.month !== monthNumber) continue

      annual.set(
        record.year,
        (annual.get(record.year) ?? 0) + record.detection_count,
      )
    }

    const current = annual.get(selectedYear) ?? 0

    // Only compare against other years with observed records.
    const baseline = [...annual.entries()]
      .filter(([recordYear]) => recordYear !== selectedYear)
      .map(([, count]) => count)

    const average = baseline.length
      ? baseline.reduce((sum, value) => sum + value, 0) / baseline.length
      : null

    const deviation = average !== null && average > 0
      ? ((current - average) / average) * 100
      : null

    return {
      month,
      current,
      average,
      deviation,
      baselineYears: baseline.length,
      hasCurrentData: annual.has(selectedYear),
    }
  })

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#101b2d] p-6">
      <div className="mb-2 flex items-center gap-2">
        <ShieldAlert size={22} className="text-orange-400" />
        <h2 className="text-xl font-bold text-white">
          Historical Anomalies
        </h2>
      </div>

      <p className="mb-3 text-sm text-slate-400">
        Monthly satellite detections compared with the historical
        average for the same calendar month.
      </p>

      <p className="mb-6 text-xs text-cyan-400">
        {sensor.toUpperCase().replaceAll('_', ' ')}
        {' · '}
        {state || 'All states'}
        {' · '}
        {selectedYear || 'No year available'}
      </p>

      {loading ? (
        <p className="py-12 text-center text-slate-400">
          Loading historical observations...
        </p>
      ) : error ? (
        <p className="py-12 text-center text-red-400">
          Unable to load historical observations.
        </p>
      ) : !availableYears.length ? (
        <p className="py-12 text-center text-slate-400">
          No historical observations available.
        </p>
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {results.map((item) => {
            const valid = item.hasCurrentData &&
              item.average !== null &&
              item.average > 0 &&
              item.baselineYears >= 2

            const deviation = valid ? item.deviation : null

            const color = deviation === null
              ? 'text-slate-400'
              : deviation > 20
                ? 'text-orange-400'
                : deviation < -20
                  ? 'text-cyan-400'
                  : 'text-slate-200'

            return (
              <div
                key={item.month}
                className="rounded-xl border border-slate-700 bg-[#080f1c] p-4"
              >
                <h3 className="font-semibold text-white">{item.month}</h3>

                <p className="mt-3 text-sm text-slate-400">
                  Selected year: {item.hasCurrentData
                    ? format(item.current)
                    : 'No observations'}
                </p>

                <p className="mt-1 text-sm text-slate-400">
                  Historical average: {item.average === null
                    ? 'N/A'
                    : format(item.average)}
                </p>

                <p className={'mt-3 text-2xl font-bold ' + color}>
                  {deviation === null
                    ? 'N/A'
                    : `${deviation > 0 ? '+' : ''}${deviation.toFixed(1)}%`}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {deviation === null
                    ? 'Insufficient comparable observations'
                    : deviation > 20
                      ? 'Above historical average'
                      : deviation < -20
                        ? 'Below historical average'
                        : 'Near historical average'}
                </p>

                <p className="mt-2 text-xs text-slate-500">
                  Baseline: {item.baselineYears} years
                </p>
              </div>
            )
          })}
        </div>
      )}

      <p className="mt-6 text-xs leading-relaxed text-slate-500">
        Descriptive historical comparison only. Baselines exclude the
        selected year and require at least two comparison years.
        Missing observations are not treated as zero.
        Percentages are not statistical significance tests, wildfire
        forecasts, or operational alerts.
      </p>
    </section>
  )
}
