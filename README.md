# FireScope AI 🔥🛰️

### From fragmented satellite fire observations to transparent, reproducible geospatial intelligence

**NASA Space Apps Challenge 2026 — Harmonization of MODIS and VIIRS Hot Spots**  
**Project status:** Historical data pipeline and experimental forecasting validation completed through **Phase 3.4**; Phase 3.5 and Phases 4–7 are proposed roadmap stages. Operational forecasting, calibrated fire-risk probabilities, production API, and interactive dashboard remain future work.

> **Scientific integrity first.** A satellite hotspot is an observation, not necessarily a unique wildfire. Detection counts are not burned area, fire severity, ignition probability, or an official warning. FireScope AI explicitly distinguishes observed detections, exploratory sensor adjustments, historical anomalies, and model estimates.

## 1. Executive overview

FireScope AI is an emerging geospatial decision-support platform designed to make long-term active-fire satellite records more understandable, traceable, and useful for research and preparedness. The project responds to a fundamental challenge: **MODIS and VIIRS observe fires differently**, with different spatial resolutions, detection sensitivities, overpass schedules, and operating histories. Simply joining their observations into one time series can introduce misleading changes in apparent fire activity.

Our response is a staged, auditable data and analytical system. It ingests NASA FIRMS observations; standardizes and audits records; associates observations with geographic regions and H3 cells; aggregates observations over time; explores cross-sensor adjustments; constructs regional seasonal baselines; detects unusual activity; and evaluates one-month-ahead satellite-detection forecasting against simple, defensible benchmarks.

The **current geographic implementation covers the United States**. The longer-term product vision includes a web dashboard for regional history, seasonality, anomalies, explicitly qualified forecasts, explanations, and advisory preparedness information. These product capabilities must not be confused with the narrower functionality already implemented.

## 2. Why the challenge matters

Satellite fire archives are exceptionally valuable, but they are not automatically comparable. Changes in hotspot counts may reflect changes in actual activity **or** changes in the observing system. This complicates long-term analysis, comparisons across regions, and decisions based on historical patterns.

FireScope AI addresses this challenge through five principles:

1. **Preserve provenance:** retain the sensor identity and source metadata throughout processing.
2. **Use consistent analytical units:** construct repeatable geographic and temporal groupings.
3. **Make harmonization testable:** estimate cross-sensor relationships using overlapping observations, with explicit scientific limitations.
4. **Prefer transparent benchmarks:** compare machine learning with historical seasonal expectations.
5. **Communicate uncertainty:** separate what is measured, adjusted, inferred, or merely proposed.

## 3. The solution: observation → context → evidence

```text
NASA FIRMS archives (MODIS, VIIRS SNPP, VIIRS NOAA-20)
                         │
             Archive inspection / USA extraction
                         │
              Provenance-aware unified data
                         │
                Quality audit / normalization
                         │
             State attribution / H3 indexing
                         │
                  Daily sensor-level activity
                         │
          Exploratory cross-sensor harmonization
                         │
            Historical fire calendar / climatology
                         │
               Leakage-aware feature engineering
                         │
                Retrospective anomaly detection
                         │
          Experimental one-month-ahead forecasting
                         │
           Independent chronological model testing
                         │
                [Planned: API + geospatial UI]
```

**Key distinction:** The cross-sensor adjustment is exploratory. It does **not** establish that MODIS and VIIRS detections have become physically equivalent, nor does it justify indiscriminate summation across sensors. Forecasting currently operates **per sensor**, using historical detection counts rather than a proven cross-sensor fire-risk target.

## 4. Implementation roadmap and phase-by-phase methodology

### Phase 1 — Data foundation and ingestion — completed

**Purpose:** establish a reproducible, provenance-preserving base dataset from NASA FIRMS archives.

- Inspect source ZIP archives and identify United States CSV members without relying on undocumented filename assumptions.
- Extract country-specific records and retain their originating sensor.
- Convert sensor datasets into efficient Parquet storage.
- Unify the schema while keeping MODIS, VIIRS SNPP, and VIIRS NOAA-20 distinguishable.
- Generate ingestion inventories and historical summaries.

**Verified project result:** **14,290,135 detections**: MODIS **2,932,997**; VIIRS SNPP **7,150,394**; VIIRS NOAA-20 **4,206,744**.

**Main output:** `data/processed/firescope_usa_unified.parquet`.

### Phase 2.1 — Data-quality assessment — completed

**Purpose:** identify invalid or suspect observations before analysis. Audit date validity, geographic coordinates, and fire radiative power (FRP) fields without silently modifying raw evidence.

**Reported result:** **2 invalid FRP values**, **0 invalid dates**, **0 invalid coordinates**. These are field-quality findings, not proof of complete satellite coverage.

**Entry point:** `backend/scripts/assess_data_quality.py`.

### Phase 2.2 — Observation normalization — completed

**Purpose:** standardize representation and analytical fields across sensors while retaining sensor-specific information and traceability.

**Output:** `data/processed/firescope_usa_normalized.parquet`.  
**Entry point:** `backend/scripts/normalize_observations.py`.

### Phase 2.3 — Geographic attribution — completed

**Purpose:** connect point detections to meaningful spatial units. Attribute observations to U.S. states and H3 resolution-5 cells, recording observations that fall outside the state polygons instead of inventing an assignment.

**Reported result:** **14,263,522** detections assigned to states; **26,613** outside the polygons; no invalid coordinates.

**Output:** `data/processed/firescope_usa_georeferenced.parquet`.  
**Entry point:** `backend/scripts/assign_geographic_regions.py`.

### Phase 2.4 — Daily activity aggregation — completed

**Purpose:** produce reproducible daily geographic/sensor-level activity summaries while retaining all underlying detections. Preserve sensor identity rather than merging incompatible raw counts.

**Reported result:** **4,213,279** aggregated groups; three unit tests passed.

**Output:** `data/processed/firescope_usa_daily_activity.parquet`.  
**Entry point:** `backend/scripts/build_daily_fire_activity.py`.

### Phase 2.5 — Exploratory MODIS/VIIRS harmonization — completed, scientifically provisional

**Purpose:** quantify systematic differences between sensors over comparable observations and test whether a documented adjustment improves alignment.

- MODIS is the numerical reference, with a scale factor of **1.0**.
- Reported exploratory factors: **0.7210570543** for VIIRS SNPP and **0.7185650208** for VIIRS NOAA-20.
- Reported held-out 2024–2025 alignment evaluation: approximately **41% improvement in log-MAE** for the specific alignment experiment.
- Preserve original sensor identities and explicitly distinguish numerical alignment from physical equivalence.

**Output:** `data/harmonized/firescope_usa_harmonized.parquet` (**4,213,279** groups).  
**Entry point:** `backend/scripts/harmonize_fire_activity.py`.

**Important:** These fitted factors are dataset- and evaluation-specific. They do not correct every source of observation bias, including orbital coverage, detection threshold, footprint, and missingness.

### Phase 2.6 — Historical fire calendar and climatology — completed

**Purpose:** characterize when satellite-observed fire activity has historically occurred, by region, month, year, and sensor. Establish interpretable seasonal reference values rather than assuming that a single national baseline describes all places.

**Reported results:** **26,047** state–year–month–sensor calendar groups and **1,838** climatology groups.

**Outputs:**

- `data/processed/firescope_usa_fire_calendar.parquet`
- `data/processed/firescope_usa_fire_climatology.parquet`

**Entry point:** `backend/scripts/build_fire_calendar.py`.

**Phase 2.7:** not implemented; the project proceeded directly to Phase 3. No completed functionality is claimed for it.

### Phase 3.1 — Leakage-aware feature engineering — completed

**Purpose:** construct reproducible inputs for historical analysis and modeling while avoiding information from the future.

- Use prior-year observations for historical seasonal features.
- Track prior-month availability explicitly.
- Distinguish missing observations from genuine observed zeros.
- Maintain separate sensor-level records.

**Reported results:** **26,047** rows; **20,571** with at least three prior-year baseline observations; **24,992** with an observed consecutive prior month; **20,529** with a historical z-score.

**Output:** `data/processed/firescope_usa_fire_features.parquet`.  
**Entry point:** `backend/scripts/build_fire_features.py`.

### Phase 3.2 — Retrospective anomaly detection — completed

**Purpose:** classify how unusual an observed monthly detection count is relative to a region- and sensor-specific historical baseline. An anomaly is **not** a probability of a wildfire or an emergency alert.

**Reported classifications:**

| Category | Rows |
| --- | ---: |
| Extreme high | 1,148 |
| High | 979 |
| Typical | 18,042 |
| Low | 260 |
| Extreme low | 100 |
| Insufficient baseline | 5,518 |
| **Total** | **26,047** |

**Output:** `data/processed/firescope_usa_fire_anomalies.parquet`.  
**Entry point:** `backend/scripts/detect_fire_anomalies.py`.

### Phase 3.3 — Experimental one-month-ahead activity forecasting — completed

**Purpose:** determine whether a simple supervised model improves on a seasonal historical mean when predicting the number of next-month satellite detections.

- Train separate **Ridge regression** models per sensor on `log1p`-transformed detection counts.
- Use lagged and historical features available at the forecast origin.
- Compare against a historical seasonal-mean baseline.
- Evaluate retrospectively on 2024–2025 observations.
- Fall back to the seasonal baseline when the model performs worse under the phase's selection rule.

**Reported outcome:** MODIS Ridge improved log-MAE by **2.16%**; VIIRS SNPP by **1.71%**; VIIRS NOAA-20 Ridge was **3.78% worse** than the seasonal baseline and the baseline was selected.

**Outputs:** `data/processed/firescope_usa_fire_forecasts.parquet` and `reports/data_quality/fire_forecasts_manifest.json`.  
**Entry point:** `backend/scripts/forecast_fire_activity.py`.

**Methodological limitation:** This phase used the 2024–2025 holdout to choose between methods and evaluate the winner; the reported selected-method performance is therefore selection-biased. Phase 3.4 addresses this design issue.

### Phase 3.4 — Independent temporal model validation — completed

**Purpose:** separate model selection from final testing, allowing a more credible estimate of generalization.

| Partition | Years | Role |
| --- | --- | --- |
| Training | Through 2021 | Fit candidate Ridge model |
| Selection | 2022–2023 | Choose Ridge or seasonal baseline |
| Independent test | 2024–2025 | Evaluate the already-selected method |

When Ridge is selected, it is refitted using observations available through 2023 before testing; 2024–2025 remains excluded from selection. This is a **retrospective rolling one-step-ahead scenario**, using observed prior-month information, not a deployed future forecast.

**User-reported execution:** three unit tests passed; **26,047 → 26,047** rows; **14,290,135** detections preserved; **3,341** independent test predictions.

| Sensor | Method selected before test | Test log-MAE | Seasonal log-MAE | Relative improvement |
| --- | --- | ---: | ---: | ---: |
| MODIS | Ridge | 0.577982 | 0.590715 | **+2.16%** |
| VIIRS SNPP | Ridge | 0.497817 | 0.506456 | **+1.71%** |
| VIIRS NOAA-20 | Ridge | 0.500977 | 0.482723 | **−3.78%** |

**Interpretation:** The independent test shows modest improvements for two sensors and deterioration for NOAA-20. **Although the phase-3.4 selection procedure chose Ridge for NOAA-20, it did not generalize better than the seasonal benchmark.** This is evidence against claiming consistent predictive superiority. These comparisons do not establish statistical significance or operational reliability.

**Output:** `data/processed/firescope_usa_fire_forecast_validation.parquet`.  
**Entry point:** `backend/scripts/validate_fire_forecasts.py`.

### Phase 3.5 — Proposed: model-readiness and scientific handoff — not implemented

**Objective:** convert the independent evaluation findings into an explicit, versioned decision about what the MVP is permitted to display. This is a **proposed scope**, not a previously agreed or completed deliverable.

**Why it is necessary:** Phase 3.4 selected Ridge for all three sensors on 2022–2023, but the independent 2024–2025 test showed that NOAA-20 Ridge was **3.78% worse** than the seasonal benchmark. A positive validation-period result is not a guarantee of generalization. The MVP therefore needs an evidence-based policy, not an unconditional "AI prediction" badge.

**Proposed implementation sequence:**

1. **Freeze evaluation artifacts.** Preserve the train/selection/test definitions, sensor-level metrics, model configuration, baseline specification, and provenance of the evaluated data. Never tune a final model on the 2024–2025 test while continuing to call that period an untouched holdout.
2. **Audit temporal availability.** Verify, for each forecast origin, that all lag and seasonal features existed at prediction time; flag gaps, short histories, sensor transitions, and incomplete coverage. Do not impute missing months as zero.
3. **Assess robustness.** Report state-level error distributions, year-by-year performance, sample sizes, and uncertainty or paired error comparisons where defensible. Treat the small MODIS/SNPP improvements as provisional until their stability is understood.
4. **Define the display policy.** For the current historical MVP, publish observations, seasonal baselines, and retrospective anomalies as the primary outputs. Show forecasting only as **experimental retrospective evaluation**, with its sensor, horizon, period, benchmark, and limitations. The NOAA-20 independent-test result must remain visible even if the validation period selected Ridge.
5. **Define machine-readable contracts.** Specify stable columns, units, null semantics, model and data versions, provenance, confidence/coverage flags, and status values for the future API. Reject unsupported claims such as "wildfire probability" or "early warning".
6. **Run a release gate.** Verify complete tests, row/detection conservation, dependency reproducibility, source-data citations, and human-readable caveats. Record any failure as a known limitation or block the corresponding feature.

**Proposed deliverables:** `docs/model-readiness.md`, `docs/data-contracts.md`, a model-evaluation summary suitable for the UI, and automated checks for temporal leakage and response contracts. **These files are planned, not currently claimed to exist.**

**Exit criterion:** an auditable MVP data contract and an explicit decision separating validated historical analytics from experimental modeling. Operational future forecasts require additional research, independent validation, and an actual future-date inference workflow.

### Phase 4 — Planned: backend API and application integration

**Objective:** expose the existing analytical products through a stable, documented interface without changing their scientific meaning.

**Work packages:**

1. **Read-only analytical service.** Implement FastAPI endpoints for supported regions, sensor metadata, monthly and daily activity, climatology, anomalies, and retrospective evaluation. Define pagination, date filters, schema validation, and meaningful empty-data responses.
2. **Query and storage layer.** Start with DuckDB querying curated Parquet artifacts; add PostgreSQL/PostGIS only if real deployment requirements justify it. Avoid introducing infrastructure merely for architectural appearance.
3. **Spatial aggregation.** Return state and H3 resolution-5 summaries with consistent geographic identifiers. Preserve sensor-specific series and provide coverage indicators so a map cannot imply comparable observations where none exist.
4. **Scientific metadata.** Include observation type, source sensor, processing date, temporal grain, baseline years, method, and caveats in API responses. Distinguish `observed`, `historical_baseline`, `retrospective_anomaly`, and `experimental_forecast` explicitly.
5. **Contract and performance tests.** Validate response schemas, numerical totals, null handling, filters, invalid inputs, and representative query latency on realistic data volumes.

**Proposed deliverables:** versioned API endpoints, OpenAPI documentation, a thin application-service layer, integration tests, and deployment configuration. **Not yet implemented or validated as a production API.**

**Exit criterion:** the frontend can retrieve consistent, sensor-aware historical insights through tested endpoints without performing data-science calculations in the browser.

### Phase 5 — Planned: interactive geospatial MVP and explanation experience

**Objective:** turn the analytical pipeline into the competition-facing experience originally proposed: a map-led, evidence-based exploration of historical fire activity.

**Proposed experience:**

1. **Explore where.** An interactive U.S. map, state selector, and optional H3 overlay show observed activity, with clear legends and time/sensor filters.
2. **Explore when.** A historical fire calendar and seasonal chart explain how observed activity changes across months and years; gaps are labeled as unavailable rather than silently shown as zero.
3. **Explore what is unusual.** Retrospective anomaly cards show the observed count, comparable historical baseline, and reason for an `insufficient_baseline` status.
4. **Understand sensor differences.** A MODIS/VIIRS comparison panel explains resolution, coverage, provenance, and the **exploratory** status of harmonization factors; it does not combine sensor counts into a physically unified wildfire total.
5. **Understand the models.** A clearly marked experimental section compares Ridge with the seasonal benchmark on the independent test, including the negative NOAA-20 result and the actual evaluation horizon.
6. **Understand implications.** Plain-language explanations and preparedness context help users interpret trends without presenting them as official fire-danger ratings, evacuation instructions, or imminent-event predictions.
7. **Accessibility and usability.** Provide readable legends, keyboard navigation, responsive layouts, loading/error states, and transparent methodology links.

**Proposed stack:** Next.js, React, TypeScript, MapLibre or an equivalent mapping library, and an accessible charting solution; the final choice should reflect team capacity and deployment constraints.

**Proposed deliverables:** responsive MVP frontend, API integration, end-to-end user journeys, accessibility checks, and an explanation panel with links to data provenance and scientific limitations.

**Exit criterion:** a reviewer can select a U.S. region, inspect NASA-derived historical observations, compare seasonal context, identify retrospective anomalies, and understand the limitations of sensor comparisons and experimental forecasts.

### Phase 6 — Planned: reproducibility, deployment, and operational safeguards

**Objective:** make the MVP independently runnable and safe to demonstrate, without claiming real-time operational fire monitoring.

**Work packages:** clean-environment dependency installation; environment-variable templates without secrets; automated tests and linting; versioned pipeline manifests; checksum-based archive provenance; build/deployment automation; API and UI smoke tests; performance checks; error logging; and a documented refresh strategy. Any future automated NASA data refresh must explicitly distinguish source latency, archive updates, missing coverage, and data-processing failures.

**Proposed deliverables:** deployment guide, reproducibility checklist, CI configuration, data-refresh runbook, and documented known limitations.

**Exit criterion:** another developer can clone the repository, obtain the documented NASA sources, reproduce the supported pipeline with the required resources, and launch a demonstrable application without relying on undocumented local state.

### Phase 7 — Planned: NASA Space Apps submission, evidence, and MVP demonstration

**Objective:** communicate a scientifically defensible solution to the challenge and demonstrate the end-to-end user journey.

**Work packages:** prepare a short demonstration showing NASA data provenance → harmonized analytical units → regional historical insights → anomaly interpretation → transparent model evaluation; document the challenge fit and target users; cite the official NASA datasets; include architecture and reproducibility instructions; disclose what is and is not implemented; and test the live demo or recorded fallback.

**Proposed deliverables:** final competition README, project summary, architecture graphic, demo video or walkthrough, reproducibility evidence, acknowledgments, and a limitations statement.

**Exit criterion:** the submission can answer **what problem was addressed, which NASA data were used, how MODIS/VIIRS differences were handled, what evidence supports the results, who benefits, and what remains future work**.

### MVP definition and release boundaries

| MVP capability | Intended phase | Evidence / acceptance condition |
| --- | --- | --- |
| Traceable NASA FIRMS ingestion and sensor-aware history | 1–2 | Archive provenance, preserved source identity, tested transformations |
| Regional seasonality and retrospective anomalies | 2.6–3.2 | Historical baselines, missingness semantics, documented thresholds |
| Independent evidence about experimental forecasts | 3.3–3.5 | Honest sensor-specific benchmark comparison and explicit limitations |
| Documented read-only API | 4 | Contract and integration tests, provenance fields |
| Interactive map, calendar, charts, explanations | 5 | Working region/sensor/time exploration and accessible UX |
| Reproducible demo deployment | 6 | Clean setup, automated checks, documented operational scope |
| Contest-ready narrative and demonstration | 7 | Data citations, clear scientific contribution, verifiable claims |

**Minimum defensible MVP:** a usable **historical satellite fire-activity intelligence dashboard** for U.S. regions, backed by NASA FIRMS observations, sensor-aware geographic and temporal analysis, seasonal context, retrospective anomalies, transparent provenance, and explicit uncertainty. **A production wildfire-risk score, calibrated ignition probability, real-time alerting, and operational future prediction are not prerequisites for this MVP and must not be implied by its branding.**

**Future research beyond the MVP:** observation-coverage normalization, additional satellite platforms, environmental covariates, forecast-origin-safe weather inputs, uncertainty calibration, multi-year external validation, broader geographic coverage, and carefully evaluated predictive targets. These are possible extensions, not committed completed features.

## 4A. NASA data provenance, authoritative sources, and reproducibility

> **Data provenance is central to this challenge.** FireScope AI does not create or independently detect satellite hotspots. Its primary observations originate from **NASA's Fire Information for Resource Management System (FIRMS)**, operated within **NASA LANCE / Earthdata**. The platform transforms those observations into traceable analytical products. NASA provides the underlying observations; the harmonization, aggregation, anomaly analysis, and experimental forecasts are FireScope AI's own derived work.

### 4A.1 Official NASA portals — where the observations come from

| Official resource | URL | Role in this project |
| --- | --- | --- |
| NASA FIRMS home | https://firms.modaps.eosdis.nasa.gov/ | Authoritative overview of the active-fire observation service. |
| **NASA FIRMS Archive Download** | **https://firms.modaps.eosdis.nasa.gov/download/** | **Primary reference for historical MODIS and VIIRS active-fire / hotspot records**, including downloadable CSV archives. |
| NASA FIRMS Active Fire Data | https://firms.modaps.eosdis.nasa.gov/active_fire/ | Recent active-fire downloads, product descriptions, and access to historical archives. |
| NASA FIRMS data availability API | https://firms.modaps.eosdis.nasa.gov/api/data_availability/ | Official sensor identifiers and availability information for standard-processing and near-real-time products. |
| NASA FIRMS NRT archive | https://nrt4.modaps.eosdis.nasa.gov/archive/FIRMS/ | Separate near-real-time distribution channel; **not evidence that the project's historical files were downloaded from this endpoint**. |

**Reproduction note:** The archive service may require an Earthdata account or email-based authentication, and archival requests may be delivered via an emailed download link. Consequently, a stable landing-page URL is not necessarily the direct URL of a particular downloaded ZIP. Do not invent a direct file URL or an acquisition timestamp when the original download receipt is unavailable.

### 4A.2 NASA observation datasets included in FireScope AI

| FireScope AI sensor label | NASA instrument / platform | NASA FIRMS product family | Nominal active-fire pixel size | Detections in the unified U.S. dataset |
| --- | --- | --- | --- | ---: |
| `modis` | **MODIS** on **Terra / Aqua** | **MODIS Collection 6.1** active-fire detections | Approximately **1 km** | **2,932,997** |
| `viirs_snpp` | **VIIRS** on **Suomi National Polar-orbiting Partnership (Suomi-NPP / S-NPP)** | **VIIRS 375 m S-NPP** active-fire detections | Approximately **375 m** | **7,150,394** |
| `viirs_noaa20` | **VIIRS** on **NOAA-20** | **VIIRS 375 m NOAA-20** active-fire detections | Approximately **375 m** | **4,206,744** |
| **Total** | Three sensor streams | Historical NASA FIRMS hotspot observations | Not directly interchangeable | **14,290,135** |

These are **detection records**, not independently confirmed wildfire events. A detection generally refers to a pixel flagged as containing an active-fire signal or thermal anomaly. A single fire may generate multiple observations, and fires may go undetected. Nominal pixel size is not a measure of fire size or burned area.

**Product-identity caution:** NASA FIRMS publishes both near-real-time (NRT) and standard-processing (SP / science-quality) products. The project history confirms use of historical FIRMS ZIP/CSV archives but does **not** provide a verified inventory of original archive filenames, download receipts, product-processing flags, or per-sensor exact acquisition windows. Accordingly, this README identifies the **authoritative product families**, but does **not** assert that every imported row is SP or name an exact source file without supporting evidence. These details should be recorded from the original archives before final contest submission.

### 4A.3 Geographic scope, lineage, and transformation chain

**Current study area:** United States. The ingestion process inspects historical source archives, extracts U.S. observations, normalizes sensor-specific fields, and retains a sensor identifier through all downstream products. Its derived outputs are:

```text
NASA FIRMS historical archive portal
  ├── MODIS Collection 6.1 active-fire records (Terra / Aqua)
  ├── VIIRS 375 m active-fire records (Suomi-NPP)
  └── VIIRS 375 m active-fire records (NOAA-20)
           │  Original downloaded archives / source CSV members
           ▼
data/raw/ [local source archives; not normally committed]
           │  Phase 1: archive inventory, U.S. extraction, schema unification
           ▼
data/processed/firescope_usa_unified.parquet
           │  Phase 2.1–2.4: quality, normalization, geography, daily aggregation
           ├── data/processed/firescope_usa_daily_activity.parquet
           │  Phase 2.5: exploratory sensor alignment (separate, documented)
           ├── data/harmonized/firescope_usa_harmonized.parquet
           │  Phase 2.6: historical monthly calendar and climatology
           ├── data/processed/firescope_usa_fire_calendar.parquet
           └── data/processed/firescope_usa_fire_climatology.parquet
                      │  Phase 3.1–3.4: features, anomalies, forecast, validation
                      ▼
              Reproducible analysis and evaluation artifacts
```

**Geographic caveat:** 14,263,522 detections were assigned to U.S. state polygons and 26,613 were outside those polygons; those records were tracked rather than silently discarded. The exact definition of the source archive's U.S. geographic subset should be verified against its CSV metadata and extraction logic; a country filter does not automatically guarantee perfect agreement with state boundary geometries.

### 4A.4 What must be recorded for a fully auditable NASA data citation

For each original downloaded archive, record the **exact filename**, **archive-request or download date**, **NASA source URL / request receipt**, **sensor**, **processing type (SP versus NRT)**, **product version**, **earliest and latest observation timestamps**, **original CSV member name**, **row count**, and **SHA-256 checksum**. This enables an independent reviewer to connect the published 14,290,135-row dataset back to specific NASA-delivered bytes. These values have **not** been reconstructed from the reported summary alone.

Recommended repository artifact: `docs/data-provenance.md` (metadata only, without authentication tokens). The original large source archives can remain outside Git while the checksums and inventory remain version-controlled.

### 4A.5 NASA attribution and responsible interpretation

**Suggested attribution:** *Source active-fire observations: NASA Fire Information for Resource Management System (FIRMS), NASA LANCE / Earthdata; MODIS Collection 6.1 and VIIRS 375 m (Suomi-NPP and NOAA-20). Derived processing, analysis, and experimental modeling: FireScope AI.*

NASA data are foundational to the project; the resulting analysis is not an official NASA forecast, endorsement, emergency alert, or validation of wildfire risk. Differences in sensor footprint, detection sensitivity, orbital coverage, clouds, and processing algorithms must be considered before interpreting apparent changes over time.

---

## 5. Software architecture

The repository follows a **Clean Architecture-oriented** organization, separating business/application orchestration from data-processing implementations and presentation concerns.

```text
FireScopeAI/                          # Git repository root; contains .git/
├── README.md                         # Main GitHub landing-page README
└── firescope-ai/                     # Application project root
    ├── backend/
    │   ├── src/firescope/
    │   │   ├── domain/               # Domain concepts and contracts
    │   │   ├── application/use_cases/ # Pipeline orchestration
    │   │   ├── infrastructure/processing/ # Transformations and modeling
    │   │   └── presentation/api/     # API scaffold / future endpoints
    │   ├── scripts/                  # CLI entry points
    │   ├── tests/unit/               # Automated tests
    │   └── pyproject.toml            # Python packaging and dependencies
    ├── data/
    │   ├── raw/                      # Original NASA archives (local)
    │   ├── processed/                # Analytical Parquet outputs
    │   └── harmonized/               # Exploratory sensor adjustments
    ├── reports/                      # Generated manifests
    └── docs/                         # Contracts and methodology

```

**Separation of concerns:** Scripts initiate workflows; application use cases coordinate tasks; infrastructure adapters execute DuckDB/Parquet processing and statistical methods; presentation should consume validated outputs rather than reproduce scientific calculations. The layout above describes the intended combined repository organization; check actual paths before publishing because the source materials include phase ZIP packages as well as an older Stage 1 repository snapshot.

**Engineering principles:** explicit provenance, reproducible outputs, sensor isolation, traceable exceptions, chronological validation, unit tests, and honest treatment of missing data. The project uses Python, DuckDB, Parquet, and scikit-learn for its implemented analytical work. Other dependencies vary by phase; confirm the installed environment and update `backend/pyproject.toml` before a clean installation is considered reproducible.

## 6. Data contracts and scientific semantics

| Concept | What it represents | What it does **not** establish |
| --- | --- | --- |
| Hotspot detection | Satellite-observed active-fire signal | A unique wildfire event |
| Detection count | Number of recorded observations | Burned area or severity |
| FRP | Sensor-derived fire radiative power | A complete severity or impact measure |
| State / H3 attribution | Spatial grouping of observation coordinates | Precise fire perimeter |
| Harmonized index / scale | Exploratory numerical adjustment | Fully corrected sensor equivalence |
| Seasonal baseline | Historical expectation for a region/sensor/season | Guaranteed future activity |
| Anomaly category | Deviation from historical observations | Fire probability or official warning |
| Ridge forecast | Retrospective estimate of satellite detections | Operational wildfire-risk probability |

No missing month should be automatically converted to zero detections. Missingness may arise from availability, coverage, filtering, or other causes. Cross-sensor comparisons require care even after numerical adjustment.

## 7. Reproducing the analytical workflow

### Prerequisites

- Python **3.11+** (the reported user validation ran on Python 3.12.3).
- NASA FIRMS ZIP archives in the documented raw-data folders.
- A Python environment with the project dependencies and phase-specific libraries installed (notably DuckDB, PyArrow, NumPy, scikit-learn, and the geographic dependencies used by the georeferencing step).
- Sufficient disk space and memory for multi-million-row datasets.

### Installation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e '.[dev]'
```

**Dependency audit required:** The Stage 1 `pyproject.toml` does not declare every library introduced in later phases. Add and pin tested dependencies before promising a fully reproducible fresh-clone installation.

### Execute the pipeline from `backend/`

```bash
# Phase 1: source inventory, ingestion, unified schema
python3 scripts/inspect_archives.py
python3 scripts/extract_usa_data.py
python3 scripts/build_unified_dataset.py

# Phase 2: quality, normalization, geography, daily activity,
#          exploratory harmonization, historical calendar
python3 scripts/assess_data_quality.py
python3 scripts/normalize_observations.py
python3 scripts/assign_geographic_regions.py
python3 scripts/build_daily_fire_activity.py
python3 scripts/harmonize_fire_activity.py
python3 scripts/build_fire_calendar.py

# Phase 3: features, anomalies, retrospective forecasting,
#          independent chronological validation
python3 scripts/build_fire_features.py
python3 scripts/detect_fire_anomalies.py
python3 scripts/forecast_fire_activity.py
python3 scripts/validate_fire_forecasts.py

# Unit tests
python3 -m pytest -q
```

**Execution note:** These commands describe the phase artifacts reviewed for this project. They assume that all phase files have been copied into the same working repository, source datasets are present, and dependencies have been installed. They have **not** been rerun end-to-end in this documentation environment.

### Data privacy and repository hygiene

Raw NASA archives, large generated Parquet datasets, virtual environments, caches, model binaries, and generated reports should not be committed by default. Commit source code, tests, configuration, reproducibility instructions, and small intentional documentation artifacts. Review `.gitignore` and the staged diff before pushing.

## 8. Validation evidence and quality gates

The reported phase executions demonstrate preservation of the 14.29-million-detection foundation across later aggregations and forecast validation. Phase 3.3 and Phase 3.4 each reported **3/3 passing unit tests**. This is encouraging engineering evidence, **not** a full scientific or operational certification.

Before public deployment, the project should verify: clean-environment installation; complete dependency declaration; independent end-to-end test execution; geographic error breakdowns; data-coverage and sensor-transition diagnostics; uncertainty intervals; robustness across years; statistical significance of marginal gains; and appropriate user-facing warnings.

## 9. Impact and value for the NASA Space Apps challenge

### Scientific value

FireScope AI creates a transparent workflow for examining the relationship between MODIS and VIIRS observations rather than assuming the sensors are interchangeable. Provenance, common geographic/temporal units, explicit calibration assumptions, and independent evaluation make cross-sensor conclusions more auditable.

### Research and education

A reproducible fire calendar and anomaly framework can help students and researchers investigate long-term seasonal patterns, compare regional behavior, and understand the difference between a detection, a statistical anomaly, and a forecast. The code and documented limitations are intended to make the analysis inspectable rather than a black box.

### Preparedness potential

A future validated interface could help land managers and emergency planners recognize unusual historical activity and identify where closer monitoring might be worthwhile. Such insights would complement—not replace—authoritative fire-danger forecasts, incident reports, emergency services, or evacuation instructions.

### Technical value

The pipeline demonstrates scalable columnar processing over **14.29 million observations**, separation of sensor-specific analyses, repeatable phase outputs, and an explicit negative result: a more complex model can perform **worse** than a simple seasonal benchmark. Reporting that failure is a meaningful contribution to responsible Earth-observation analytics.

### What is demonstrated versus what remains aspirational

**Demonstrated:** USA data ingestion, auditing, normalization, state/H3 attribution, temporal aggregation, exploratory harmonization, climatology, anomalies, experimental forecasting, and chronological model evaluation.

**Not yet demonstrated:** a validated global harmonization standard, corrected orbital coverage, wildfire occurrence probabilities, operational early warnings, wildfire severity estimation, live monitoring, production map dashboard, weather/vegetation-based causal explanations, or measured reduction in real-world fire impacts.

## 10. Product vision and future extensions

The project vision envisages an interactive geographic dashboard answering four questions: **What is happening? When does it usually happen? Where may activity intensify next? How should stakeholders prepare?** The planned user experience combines a map, historical calendar, regional activity trends, explainable forecasts, and contextual preparedness guidance.

Longer-term research could add weather and vegetation covariates, explicit coverage correction, calibrated event-probability targets, multi-horizon evaluation, uncertainty quantification, and expansion beyond the United States. Any such extension must use only features available at the actual forecast origin and must be independently evaluated before its output is described as risk or probability.

Reinforcement learning is **not** part of the current MVP: responsible resource-allocation optimization would require a defensible simulation environment and historical decision/outcome evidence.

## 11. Responsible use and limitations

- Satellite detection coverage varies with sensor characteristics, orbit, cloud/smoke conditions, and processing choices.
- Numerical sensor alignment is not proof of identical measurement processes.
- Historical anomalies are descriptive, not predictive probabilities.
- The Phase 3.4 test is retrospective; its reported one-step scenario uses the observed prior month.
- Small positive gains for MODIS and VIIRS SNPP do not prove reliable operational performance.
- NOAA-20 Ridge underperformed the seasonal baseline on the independent test.
- No automated evacuation, emergency dispatch, or official warning decisions should be made from these outputs.

## 12. Repository publication checklist

Before pushing to GitHub (run Git commands from the **outer `FireScopeAI/` repository root**, which contains `.git/`; keep this README at **`FireScopeAI/README.md`** so GitHub displays it on the repository landing page):

1. Merge the Phase 1 repository with all implemented Phase 2 and Phase 3 source files and tests.
2. Update `backend/pyproject.toml` for every actually imported runtime/test dependency.
3. Ensure `.gitignore` excludes datasets, secrets, caches, local environments, and generated artifacts.
4. Run all tests and, where feasible, lint checks; investigate failures rather than suppressing them.
5. Verify that documentation describes **implemented** features separately from the roadmap.
6. Review `git status` and `git diff --cached --stat` before committing.
7. Push to the intended remote only after confirming its URL and branch.

## 13. Project provenance

**Challenge:** NASA Space Apps Challenge 2026 — *Harmonization of MODIS and VIIRS Hot Spots*.  
**Primary data family:** NASA FIRMS active-fire observations from MODIS and VIIRS.  
**Current implementation:** United States historical observations.  
**Official NASA data access:** https://firms.modaps.eosdis.nasa.gov/download/ (historical archive); https://firms.modaps.eosdis.nasa.gov/active_fire/ (product descriptions and recent data).  
**Development approach:** phased delivery, Clean Architecture, reproducible data processing, sensor-aware validation, and transparent scientific limitations.

*This README reflects the project proposal, continuity notes, available phase-code packages, and reported pipeline/test outputs reviewed before Phase 4. It does not claim that a production system or independent deployment audit has been completed.*
