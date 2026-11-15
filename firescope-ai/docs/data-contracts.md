# FireScope AI — MVP data contracts (Phase 3.5)

**Contract version:** `1.0.0` — specifications for Phase 4 API; these endpoints are **not yet implemented**.

## Scientific invariants

- `sensor`: one of `modis`, `viirs_snpp`, `viirs_noaa20`; do not sum across sensors as if physically equivalent.
- `state_code`: U.S. state identifier from georeferencing; null/outside-boundary observations require explicit treatment.
- `year`: integer, `month`: integer 1–12; month is calendar month, not a detection timestamp.
- `detection_count`: nonnegative integer **satellite detections**, not unique fires.
- `historical_mean`: nullable nonnegative float, calculated using strictly earlier eligible years; null means insufficient baseline, not zero.
- `independent_forecast_detection_count`: nullable nonnegative float, **retrospective** experimental estimate for eligible 2024–2025 test rows only; null means no estimate.
- `independent_forecast_status`: one of `outside_test`, `insufficient_features`, `independent_test_prediction` in the Phase 3.4 output.
- `independent_test_predictions`: number of non-null retrospective predictions; not a count of forecasted real-world fires.

## Proposed API representation (Phase 4)

Each response should expose `schema_version`, `data_source`, `sensor`, `geography`, `time_window`, `metric`, `unit`, `value`, `status`, `coverage`, `limitations`, and `provenance`. Nullable values must remain JSON `null`; missing months must not be fabricated as zeros. Add pagination and maximum query windows for large series.

### Readiness summary

`reports/data_quality/model_readiness_manifest.json` provides:

- `schema_version`, `release_gate`, `split`;
- `source_sha256`, `validation_manifest_sha256`;
- `row_count`, `detections_preserved`, `independent_test_predictions`;
- `sensor_results.{sensor}.independent_test`, `by_year`, `by_state`, `selection_method`;
- `display_policy.allowed`, `display_policy.prohibited`, `release_checks`, `limitations`.

**Units:** error metrics are mean absolute error in `log1p(detection_count)` space; relative improvement is a ratio (multiply by 100 for percent). The API must not call this a fire-risk score or calibrated probability.

## API release gates

1. Verify schema/version, units, null semantics and sensor separation.
2. Publish provenance and scientific caveats in each relevant response.
3. Reject queries that would imply unsupported risk probabilities or operational future predictions.
4. Test missing months, empty subgroups, duplicate keys, malformed dates, and performance.
5. Do not claim temporal leakage has been ruled out until upstream point-in-time availability is audited.
