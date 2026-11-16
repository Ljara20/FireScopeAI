import { BarChart3, CalendarRange } from 'lucide-react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import type { CalendarRecord, Sensor } from '../../lib/api'
import { useHistoricalData } from '../../hooks/useHistoricalData'

type Props = {
  sensor: Sensor
  state: string
  year: string
}

const months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
]

const formatNumber = (value: number) =>
  new Intl.NumberFormat('en-US').format(value)

function aggregateMonthly(records: CalendarRecord[]) {
  return months.map((month, index) => ({
    month,
    detections: records
      .filter((record) => record.month === index + 1)
      .reduce((total, record) => total + record.detection_count, 0),
  }))
}

export function TrendsPanel({ sensor, state, year }: Props) {
  const query = useHistoricalData(sensor, year)
  const loading = query.isPending || query.isFetching
  const error = query.isError

  const records = !loading && !error
    ? query.data.filter(
        (record) => !state || record.state_code === state,
      )
    : []

  const data = aggregateMonthly(records)
  const total = data.reduce((sum, item) => sum + item.detections, 0)

  return (
    <section className="flex min-h-96 flex-col rounded-2xl border border-slate-800 bg-[#101b2d] p-5">
      <div className="flex items-center gap-2">
        <BarChart3 size={19} className="text-cyan-400" />
        <h3 className="font-semibold text-white">
          Historical Trends
        </h3>
      </div>

      <p className="mt-2 text-xs text-slate-400">
        Monthly satellite hotspot detections
      </p>

      <p className="mt-3 text-xs text-cyan-400">
        {sensor.toUpperCase().replaceAll('_', ' ')}
        {' · '}
        {state || 'All states'}
        {' · '}
        {year || 'All available years'}
      </p>

      <div className="my-5 flex min-h-64 flex-1 items-center justify-center rounded-xl border border-slate-700 bg-[#080f1c] p-3">
        {loading ? (
          <p className="text-sm text-slate-400">Loading historical data...</p>
        ) : error ? (
          <p className="text-sm text-red-400">
            Unable to load historical data.
          </p>
        ) : total === 0 ? (
          <p className="text-sm text-slate-400">
            No detections found for these filters.
          </p>
        ) : (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 12, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid
                  stroke="#26354a"
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis
                  dataKey="month"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 10 }}
                  tickFormatter={(value: number) =>
                    Intl.NumberFormat('en-US', {
                      notation: 'compact',
                    }).format(value)
                  }
                  axisLine={false}
                  tickLine={false}
                  width={42}
                />
                <Tooltip
                  formatter={(value) => [
                    formatNumber(Number(value ?? 0)),
                    'Detections',
                  ]}
                  contentStyle={{
                    backgroundColor: '#101b2d',
                    border: '1px solid #334155',
                    borderRadius: 10,
                    color: '#fff',
                  }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar
                  dataKey="detections"
                  fill="#f97316"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={32}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      <p className="mb-3 text-xs text-slate-400">
        {loading || error
          ? 'Total detections: —'
          : `Total detections: ${formatNumber(total)}`}
      </p>

      <div className="flex items-center gap-2 text-xs text-slate-500">
        <CalendarRange size={15} />
        Historical observations only · No operational forecasts
      </div>
    </section>
  )
}
