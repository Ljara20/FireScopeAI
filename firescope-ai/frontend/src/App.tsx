import { useState } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { MetricCards } from './components/dashboard/MetricCards'
import { MapPanel } from './components/dashboard/MapPanel'
import { TrendsPanel } from './components/dashboard/TrendsPanel'
import {
  DashboardFilters,
  type DashboardFilterValues,
} from './components/filters/DashboardFilters'

function App() {
  const [filters, setFilters] = useState<DashboardFilterValues>({
    sensor: 'modis',
    state: '',
    year: '',
  })

  return (
    <div className="min-h-screen bg-[#080f1c] text-slate-100 lg:flex">
      <Sidebar />

      <div className="min-w-0 flex-1">
        <Header />

        <main className="space-y-6 p-4 sm:p-6">
          <DashboardFilters filters={filters} onChange={setFilters} />

          <MetricCards sensor={filters.sensor} state={filters.state} year={filters.year} />

          <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
            <MapPanel
              sensor={filters.sensor}
              state={filters.state}
              year={filters.year}
              onSelectState={(state) =>
                setFilters((current) => ({ ...current, state }))
              }
            />

            <TrendsPanel
              sensor={filters.sensor}
              year={filters.year}
            />
          </div>

          <p className="text-xs text-slate-500">
            Interface preview · No live backend data connected yet.
          </p>
        </main>
      </div>
    </div>
  )
}

export default App
