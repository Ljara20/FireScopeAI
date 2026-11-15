# FireScope AI — Phase 3.5: Scientific model-readiness decision

**Status:** Implemented as an auditable retrospective readiness assessment; operational forecasting **not approved**.

## Inputs and reproducibility

- `data/processed/firescope_usa_fire_forecast_validation.parquet` (Phase 3.4)
- `reports/data_quality/fire_forecast_validation_manifest.json` (Phase 3.4)
- SHA-256 digests of both inputs are recorded in the Phase 3.5 output.
- Phase 3.4 temporal protocol: train before 2022; select on 2022–2023; independently test on 2024–2025. Ridge is refitted on pre-test observations if selected.

## Evidence and decision

Reported Phase 3.4 independent test results:

| Sensor | Selected on 2022–2023 | 2024–2025 Ridge/selected log-MAE | Seasonal log-MAE | Relative improvement |
| --- | --- | ---: | ---: | ---: |
| MODIS | Ridge | 0.57798184 | 0.59071450 | +2.16% |
| VIIRS S-NPP | Ridge | 0.49781659 | 0.50645622 | +1.71% |
| VIIRS NOAA-20 | Ridge | 0.50097741 | 0.48272264 | **−3.78%** |

The modest gains for two sensors are not evidence of statistically significant or operationally reliable prediction. The negative NOAA-20 result must remain visible; the independent test must not be reused for model selection while being described as untouched.

## Release gate

**Allowed for the MVP:** historical detections, climatological baselines, retrospective anomalies, and explicitly labeled *experimental retrospective model evaluation*. Display the selected model, test period, per-sensor error and seasonal benchmark. State-level and yearly metrics must carry sample sizes.

**Not allowed:** wildfire probability, unique fire counts, severity, burned area, operational early warning, or validated future-date forecasts.

## Known limitations and required follow-up

1. The pipeline has not demonstrated that every historical seasonal feature and lag was available at the forecast origin. The script checks that predictions appear only in the test years, **not** full upstream point-in-time provenance. An upstream lineage audit remains mandatory before operational claims.
2. Missing observations are not equivalent to zero fire activity; satellite overpass/coverage effects are not corrected.
3. Model performance is conditional on rows with eligible historical features; sparse states and years can yield unstable subgroup errors.
4. No statistical significance test or calibrated prediction interval is claimed.
5. The output is a readiness **report**, not a new predictive model and not an API implementation.

## Execution

From `firescope-ai/backend`:

```bash
python3 -m pytest tests/unit/test_model_readiness.py -vv
python3 scripts/prepare_model_readiness.py
```

Output: `reports/data_quality/model_readiness_manifest.json` (locally generated, intentionally excluded from Git).
