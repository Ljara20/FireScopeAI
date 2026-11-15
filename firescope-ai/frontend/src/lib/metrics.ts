import type { CalendarRecord } from './api'

export interface HistoricalMetrics {
  detections: number
  frpMw: number | null
  observedYears: number
  daysWithDetections: number | null
}

export function calculateMetrics(
  records: CalendarRecord[],
  stateCode: string,
): HistoricalMetrics {
  const detections = records.reduce(
    (sum, record) => sum + record.detection_count,
    0,
  )

  const validFrpRecords = records.filter(
    (record) => record.valid_frp_count > 0 &&
      record.frp_sum_mw !== null,
  )

  const frpMw = validFrpRecords.length
    ? validFrpRecords.reduce(
        (sum, record) => sum + (record.frp_sum_mw ?? 0),
        0,
      )
    : null

  const observedYears = new Set(
    records.map((record) => record.year),
  ).size

  // Monthly days can be summed within one state because
  // calendar months do not overlap.
  // Across states, the same date may appear multiple times.
  const daysWithDetections = stateCode
    ? records.reduce(
        (sum, record) => sum + record.days_with_detections,
        0,
      )
    : null

  return {
    detections,
    frpMw,
    observedYears,
    daysWithDetections,
  }
}
