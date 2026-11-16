import { Suspense, lazy, useState } from 'react'
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'
import {
  DashboardFilters,
  type DashboardFilterValues,
} from './components/filters/DashboardFilters'

const MetricCards = lazy(() => import('./components/dashboard/MetricCards').then((module) => ({ default: module.MetricCards })))
const MapPanel = lazy(() => import('./components/dashboard/MapPanel').then((module) => ({ default: module.MapPanel })))
const TrendsPanel = lazy(() => import('./components/dashboard/TrendsPanel').then((module) => ({ default: module.TrendsPanel })))
const FireCalendar = lazy(() => import('./components/dashboard/FireCalendar').then((module) => ({ default: module.FireCalendar })))
const HistoricalAnomalies = lazy(() => import('./components/dashboard/HistoricalAnomalies').then((module) => ({ default: module.HistoricalAnomalies })))
const ExperimentalModel = lazy(() => import('./components/dashboard/ExperimentalModel').then((module) => ({ default: module.ExperimentalModel })))

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
        <Header activePage={activePage} />

        <main className="space-y-6 p-4 sm:p-6">
          <DashboardFilters filters={filters} onChange={setFilters} />

          <Suspense fallback={
            <div role="status" className="rounded-2xl border border-slate-800 bg-[#101b2d] p-8 text-sm text-slate-400">
              Loading section...
            </div>
          }>
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

          </Suspense>

          <p className="text-xs text-slate-500">
            Historical NASA FIRMS observations · Not real-time monitoring or wildfire forecasts.
          </p>
        </main>
      </div>
    </div>
  )
}

export default App
