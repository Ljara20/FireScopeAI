import { Filter } from 'lucide-react'

export type DashboardFilterValues = {
  sensor: string
  state: string
  year: string
}

type Props = {
  filters: DashboardFilterValues
  onChange: (filters: DashboardFilterValues) => void
}

export function DashboardFilters({ filters, onChange }: Props) {
  const update = (key: keyof DashboardFilterValues, value: string) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <section className="rounded-2xl border border-slate-800 bg-[#101b2d] p-5">
      <div className="mb-4 flex items-center gap-2">
        <Filter size={18} className="text-orange-400" />
        <h3 className="font-semibold text-white">Explore Historical Data</h3>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <label className="space-y-2 text-sm text-slate-300">
          <span className="block">Satellite sensor</span>
          <select
            value={filters.sensor}
            onChange={(event) => update('sensor', event.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-[#080f1c] p-3 text-white"
          >
            <option value="modis">MODIS Terra/Aqua</option>
            <option value="viirs_snpp">VIIRS SNPP</option>
            <option value="viirs_noaa20">VIIRS NOAA-20</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-300">
          <span className="block">State</span>
          <select
            value={filters.state}
            onChange={(event) => update('state', event.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-[#080f1c] p-3 text-white"
          >
            <option value="">All states</option>
            <option value="CA">California</option>
            <option value="TX">Texas</option>
            <option value="FL">Florida</option>
            <option value="OR">Oregon</option>
            <option value="WA">Washington</option>
          </select>
        </label>

        <label className="space-y-2 text-sm text-slate-300">
          <span className="block">Year</span>
          <select
            value={filters.year}
            onChange={(event) => update('year', event.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-[#080f1c] p-3 text-white"
          >
            <option value="">All available years</option>
            {Array.from({ length: 27 }, (_, index) => 2026 - index).map(
              (year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ),
            )}
          </select>
        </label>
      </div>
    </section>
  )
}
