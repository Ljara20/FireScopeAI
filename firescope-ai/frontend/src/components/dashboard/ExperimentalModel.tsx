import { useQuery } from '@tanstack/react-query'
import { ChartNoAxesCombined } from 'lucide-react'
import {
  ResponsiveContainer, BarChart, Bar,
  CartesianGrid, XAxis, YAxis, Tooltip, Legend,
} from 'recharts'
import { getAllForecasts, type Sensor } from '../../lib/api'

type Props = {
  sensor: Sensor
  state: string
  year: string
}

const format = (value: number) =>
  new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 1,
  }).format(value)

export function ExperimentalModel({ sensor, state, year }: Props) {
  const query = useQuery({
    queryKey: ['experimental-model', sensor, state, year],
    queryFn: () =>
      getAllForecasts(sensor, state, year ? Number(year) : undefined),
  })

  const loading = query.isPending || query.isFetching
  const error = query.isError

  const valid = !loading && !error
    ? query.data.filter(
        (record) =>
          record.independent_forecast_status ===
            'independent_test_prediction' &&
          record.independent_forecast_detection_count !== null,
      )
    : []

  const monthly = Array.from({ length: 12 }, (_, index) => {
    const matching = valid.filter((record) => record.month === index + 1)

    return {
      month: new Date(2024, index, 1).toLocaleString('en-US', {
        month: 'short',
      }),
      observed: matching.reduce(
        (sum, record) => sum + record.detection_count, 0,
      ),
      estimated: matching.reduce(
        (sum, record) =>
          sum + (record.independent_forecast_detection_count ?? 0), 0,
      ),
    }
  })

  const mae = valid.length
    ? valid.reduce(
        (sum, record) =>
          sum + Math.abs(
            record.detection_count -
            (record.independent_forecast_detection_count ?? 0),
          ),
        0,
      ) / valid.length
    : null

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#101b2d] p-6">
      <div className="mb-2 flex items-center gap-2">
        <ChartNoAxesCombined size={22} className="text-orange-400" />
        <h2 className="text-xl font-bold text-white">
          Experimental Model
        </h2>
      </div>

      <p className="mb-4 text-sm text-slate-400">
        Retrospective independent-test estimates compared with
        historical satellite observations.
      </p>

      <p className="mb-6 text-xs text-cyan-400">
        {sensor.toUpperCase().replaceAll('_', ' ')}
        {' · '}
        {state || 'All states'}
        {' · '}
        {year || 'All available years'}
      </p>

      {loading ? (
        <p className="py-12 text-center text-slate-400">
          Loading model evaluation data...
        </p>
      ) : error ? (
        <p className="py-12 text-center text-red-400">
          Unable to load model evaluation data.
        </p>
      ) : valid.length === 0 ? (
        <p className="py-12 text-center text-slate-400">
          No independent-test estimates available for these filters.
        </p>
      ) : (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-slate-700 bg-[#080f1c] p-5">
              <p className="text-sm text-slate-400">
                Independent-test observations
              </p>
              <p className="mt-2 text-2xl font-bold text-white">
                {format(valid.length)}
              </p>
            </div>

            <div className="rounded-xl border border-slate-700 bg-[#080f1c] p-5">
              <p className="text-sm text-slate-400">
                Mean Absolute Error
              </p>
              <p className="mt-2 text-2xl font-bold text-orange-400">
                {mae === null ? 'N/A' : format(mae)}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Satellite detections per state-month
              </p>
            </div>
          </div>

          <div className="h-80 rounded-xl border border-slate-700 bg-[#080f1c] p-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly}>
                <CartesianGrid
                  stroke="#26354a"
                  strokeDasharray="3 3"
                  vertical={false}
                />
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  formatter={(value) => format(Number(value ?? 0))}
                  contentStyle={{
                    backgroundColor: '#101b2d',
                    border: '1px solid #334155',
                    color: '#fff',
                  }}
                />
                <Legend />
                <Bar dataKey="observed" fill="#f97316" name="Observed" />
                <Bar dataKey="estimated" fill="#22d3ee" name="Estimated" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      <p className="mt-6 text-xs leading-relaxed text-slate-500">
        Experimental retrospective evaluation only.
        Estimates are not future forecasts, wildfire probabilities,
        or operational alerts. Satellite detections are not
        individual wildfires. MAE is calculated from the
        independent-test records matching the selected filters.
      </p>
    </section>
  )
}
