import { useEffect, useMemo, useState } from 'react'
import { geoAlbersUsa, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import type { FeatureCollection, Geometry } from 'geojson'
import type { Topology } from 'topojson-specification'
import { MapPinned } from 'lucide-react'
import { getAllCalendar, getRegions } from '../../lib/api'
import type { Sensor } from '../../lib/api'
import { normalizeStateName } from '../../lib/stateNames'

type Props = {
  sensor: Sensor
  state: string
  year: string
  onSelectState: (state: string) => void
}

type StateProperties = { name: string }
type StateFeature = FeatureCollection<Geometry, StateProperties>

export function MapPanel({ sensor, state, year, onSelectState }: Props) {
  const [geography, setGeography] = useState<StateFeature | null>(null)
  const [totals, setTotals] = useState<Record<string, number>>({})
  const [names, setNames] = useState<Record<string, string>>({})
  const [hovered, setHovered] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    fetch('/geo/us-states.json')
      .then((response) => {
        if (!response.ok) throw new Error('Geography unavailable')
        return response.json() as Promise<Topology>
      })
      .then((topology) => {
        setGeography(
          feature(topology, topology.objects.states) as StateFeature,
        )
      })
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    let active = true

    Promise.all([
      getRegions(sensor),
      getAllCalendar(sensor, '', year ? Number(year) : undefined),
    ])
      .then(([regions, records]) => {
        if (!active) return

        const codes: Record<string, string> = {}
        const stateNames: Record<string, string> = {}

        for (const region of regions.regions) {
          codes[normalizeStateName(region.state_name)] = region.state_code
          stateNames[region.state_code] = region.state_name
        }

        const counts: Record<string, number> = {}

        for (const record of records) {
          if (!record.state_code) continue
          counts[record.state_code] =
            (counts[record.state_code] ?? 0) + record.detection_count
        }

        const mapped: Record<string, number> = {}

        for (const [name, code] of Object.entries(codes)) {
          if (code in counts) mapped[name] = counts[code]
        }

        setTotals(mapped)
        setNames(codes)
        setLoading(false)
        setError(false)
      })
      .catch(() => {
        if (active) {
          setLoading(false)
          setError(true)
        }
      })

    return () => {
      active = false
    }
  }, [sensor, year])

  const paths = useMemo(() => {
    if (!geography) return []

    const projection = geoAlbersUsa().fitSize([960, 600], geography)
    const generator = geoPath(projection)

    return geography.features.map((item) => ({
      name: item.properties.name,
      path: generator(item) ?? '',
    }))
  }, [geography])

  const maximum = Math.max(1, ...Object.values(totals))

  function fill(name: string) {
    const value = totals[normalizeStateName(name)]

    if (value === undefined) return '#263449'

    const intensity = Math.log1p(value) / Math.log1p(maximum)

    if (intensity > 0.8) return '#f97316'
    if (intensity > 0.6) return '#ea580c'
    if (intensity > 0.4) return '#c2410c'
    if (intensity > 0.2) return '#7c2d12'
    return '#43302c'
  }

  const hoveredName = hovered ?? ''
  const hoveredCode = names[normalizeStateName(hoveredName)]
  const hoveredTotal = totals[normalizeStateName(hoveredName)]

  return (
    <section className="flex min-h-96 flex-col rounded-2xl border border-slate-800 bg-[#101b2d] p-5">
      <div className="flex items-center gap-2">
        <MapPinned size={19} className="text-orange-400" />
        <h3 className="font-semibold text-white">Geographic Exploration</h3>
      </div>

      <p className="mt-2 text-xs text-slate-400">
        United States · Historical satellite hotspot detections · {sensor.toUpperCase()}
      </p>

      <div className="mt-5 flex-1 rounded-xl bg-[#080f1c] p-3">
        {loading && <p className="text-sm text-slate-400">Loading observations...</p>}
        {error && <p className="text-sm text-red-400">Map data unavailable.</p>}

        <svg
          viewBox="0 0 960 600"
          className="h-auto w-full"
          role="img"
          aria-label="United States historical satellite detection map"
        >
          {paths.map(({ name, path }) => {
            const code = names[normalizeStateName(name)]
            const selected = code === state

            return (
              <path
                key={name}
                d={path}
                fill={fill(name)}
                stroke={selected ? '#67e8f9' : '#64748b'}
                strokeWidth={selected ? 2.5 : 0.7}
                className={code ? 'cursor-pointer transition-colors' : ''}
                onMouseEnter={() => setHovered(name)}
                onMouseLeave={() => setHovered(null)}
                onClick={() => {
                  if (code) onSelectState(selected ? '' : code)
                }}
              >
                <title>
                  {name}: {totals[normalizeStateName(name)]?.toLocaleString() ?? 'No observations'}
                </title>
              </path>
            )
          })}
        </svg>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="text-slate-300">
          {hovered
            ? `${hoveredName}${hoveredCode ? ` (${hoveredCode})` : ''}: ${
                hoveredTotal === undefined
                  ? 'No observations'
                  : hoveredTotal.toLocaleString() + ' detections'
              }`
            : `Selected geography: ${state || 'All states'}`}
        </div>

        <div className="flex items-center gap-2 text-slate-400">
          <span>Historical detections:</span>
          <span>Fewer</span>
          {['#43302c', '#7c2d12', '#c2410c', '#ea580c', '#f97316'].map(
            (color) => (
              <span
                key={color}
                className="h-3 w-4 rounded-sm"
                style={{ backgroundColor: color }}
              />
            ),
          )}
          <span>More</span>
          <span className="text-slate-500">
            (max: {maximum.toLocaleString()})
          </span>
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Counts represent satellite detections, not unique fires or operational risk.
        Gray areas have no observations in the selected dataset.
      </p>
    </section>
  )
}
