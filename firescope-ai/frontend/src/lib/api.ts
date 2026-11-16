export type Sensor = 'modis' | 'viirs_snpp' | 'viirs_noaa20'

export interface Region {
  state_code: string
  state_name: string
}

export interface RegionsResponse {
  schema_version: string
  sensor: Sensor
  regions: Region[]
  count: number
  limitations: string[]
}

export interface CalendarRecord {
  state_code: string | null
  state_name: string | null
  sensor: Sensor
  year: number
  month: number
  month_start: string
  days_with_detections: number
  detection_count: number
  valid_frp_count: number
  invalid_frp_count: number
  frp_sum_mw: number | null
  median_daily_cell_aligned_log_activity: number | null
  aligned_daily_cell_groups: number
  alignment_status: string
}

export interface CalendarResponse {
  schema_version: string
  sensor: Sensor
  metric: string
  unit: string
  records: CalendarRecord[]
  count: number
  limit: number
  offset: number
  limitations: string[]
}

async function apiGet<T>(
  path: string,
  params: Record<string, string | number>,
): Promise<T> {
  const search = new URLSearchParams()

  for (const [key, value] of Object.entries(params)) {
    search.set(key, String(value))
  }

  const response = await fetch(`${path}?${search.toString()}`)

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function getRegions(sensor: Sensor) {
  return apiGet<RegionsResponse>('/api/v1/regions', { sensor })
}

export function getCalendar(
  sensor: Sensor,
  stateCode: string,
  year: number,
  limit = 100,
  offset = 0,
) {
  return apiGet<CalendarResponse>('/api/v1/calendar', {
    sensor,
    state_code: stateCode,
    year,
    limit,
    offset,
  })
}

export async function getAllCalendar(
  sensor: Sensor,
  stateCode = '',
  year?: number,
): Promise<CalendarRecord[]> {
  const records: CalendarRecord[] = []
  const limit = 1000

  for (let offset = 0; ; offset += limit) {
    const params: Record<string, string | number> = {
      sensor,
      limit,
      offset,
    }

    if (stateCode) params.state_code = stateCode
    if (year !== undefined) params.year = year

    const page = await apiGet<CalendarResponse>(
      '/api/v1/calendar',
      params,
    )

    records.push(...page.records)

    if (page.records.length < limit) break
  }

  return records
}


export interface ForecastRecord {
  state_code: string | null
  state_name: string | null
  sensor: Sensor
  year: number
  month: number
  feature_month: string
  detection_count: number
  independent_forecast_detection_count: number | null
  independent_forecast_status:
    | 'independent_test_prediction'
    | 'insufficient_features'
    | 'outside_test'
  baseline_years: number
  has_minimum_baseline: boolean
  has_consecutive_previous_month: boolean
}

export interface ForecastsResponse {
  records: ForecastRecord[]
  count: number
  limitations: string[]
}

export async function getAllForecasts(
  sensor: Sensor,
  stateCode = '',
  year?: number,
): Promise<ForecastRecord[]> {
  const records: ForecastRecord[] = []
  const limit = 1000

  for (let offset = 0; ; offset += limit) {
    const params: Record<string, string | number> = {
      sensor,
      limit,
      offset,
    }

    if (stateCode) params.state_code = stateCode
    if (year !== undefined) params.year = year

    const page = await apiGet<ForecastsResponse>(
      '/api/v1/forecasts',
      params,
    )

    records.push(...page.records)

    if (page.records.length < limit) break
  }

  return records
}
