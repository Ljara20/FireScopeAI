import { useState } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import { MetricCards } from './components/dashboard/MetricCards'
import { MapPanel } from './components/dashboard/MapPanel'
import { TrendsPanel } from './components/dashboard/TrendsPanel'
import { FireCalendar } from './components/dashboard/FireCalendar'
import { HistoricalAnomalies } from './components/dashboard/HistoricalAnomalies'
import { ExperimentalModel } from './components/dashboard/ExperimentalModel'
import {
  DashboardFilters,
  type DashboardFilterValues,
} from './components/filters/DashboardFilters'

function App() {
  const [activePage, setActivePage] = useState('Overview')
  const [filters, setFilters] = useState<DashboardFilterValues>({
    sensor: 'modis',
    state: '',
    year: '',
  })

  return (
    <div className="min-h-screen bg-[#080f1c] text-slate-100 lg:flex">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      <div className="min-w-0 flex-1">
        <Header />

        <main className="space-y-6 p-4 sm:p-6">
          <DashboardFilters filters={filters} onChange={setFilters} />

          {activePage === 'Overview' ? (
            <>
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
              state={filters.state}
              year={filters.year}
            />
          </div>

            </>
          ) : activePage === 'Fire Calendar' ? (
            <FireCalendar
              sensor={filters.sensor}
              state={filters.state}
              year={filters.year}
            />
          ) : activePage === 'Historical Anomalies' ? (
            <HistoricalAnomalies
              sensor={filters.sensor}
              state={filters.state}
              year={filters.year}
            />
          ) : activePage === 'Experimental Model' ? (
            <ExperimentalModel
              sensor={filters.sensor}
              state={filters.state}
              year={filters.year}
            />
          ) : (
            <section className="rounded-2xl border border-slate-800 bg-[#101b2d] p-8">
              <h2 className="text-xl font-bold text-white">
                {activePage}
              </h2>
              <p className="mt-3 text-sm text-slate-400">
                This section is planned for a future development phase.
              </p>
            </section>
          )}

          <p className="text-xs text-slate-500">
            Historical NASA FIRMS observations · Not real-time monitoring or wildfire forecasts.
          </p>
        </main>
      </div>
    </div>
  )
}

export default App
