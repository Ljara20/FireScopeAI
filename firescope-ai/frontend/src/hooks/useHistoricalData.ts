import { useQuery } from '@tanstack/react-query'
import { getAllCalendar, getRegions, type Sensor } from '../lib/api'

export function useHistoricalData(sensor: Sensor, year: string) {
  return useQuery({
    queryKey: ['historical-calendar', sensor, year],
    queryFn: () =>
      getAllCalendar(sensor, '', year ? Number(year) : undefined),
  })
}

export function useRegions(sensor: Sensor) {
  return useQuery({
    queryKey: ['regions', sensor],
    queryFn: () => getRegions(sensor),
  })
}
