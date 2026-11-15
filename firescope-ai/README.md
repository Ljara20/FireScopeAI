# FireScope AI 🔥🛰️

NASA Space Apps Challenge 2026 — **Harmonization of MODIS and VIIRS Hot Spots**.

**Stage 1 implemented:** inspect NASA FIRMS ZIP archives, extract only the United States country CSV, preserve source metadata, write sensor-specific Parquet, build a schema-unified Parquet and a monthly raw-observation report. **Scientific harmonization, prediction and frontend are not implemented yet.**

## Requirements
Python 3.11+, Git, VS Code. Works on Windows, macOS and Linux.

## Setup (VS Code terminal)
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```
On macOS/Linux: `source .venv/bin/activate`.

## Where to place NASA ZIP files
```text
data/raw/modis/modis_2000_all_countries.zip
data/raw/modis/modis_2001_all_countries.zip
...
data/raw/viirs_snpp/viirs-snpp_2012_all_countries.zip
...
data/raw/viirs_noaa20/viirs-jpss1_2018_all_countries.zip
```
Keep ZIP files compressed. ZIP contents must contain USA country CSVs. Inspect actual internal names first.

## Run from backend/ with activated virtual environment
```powershell
python scripts/inspect_archives.py
python scripts/extract_usa_data.py
python scripts/build_unified_dataset.py
python -m pytest -q
python -m ruff check src scripts tests
```

Outputs:
- `reports/archive_inventory.json`: ZIP inventory, USA members and unmatched filename examples.
- `reports/ingestion_report.json`: per-sensor counts and warnings.
- `data/processed/modis_usa.parquet`
- `data/processed/viirs_snpp_usa.parquet`
- `data/processed/viirs_noaa20_usa.parquet`
- `data/processed/firescope_usa_unified.parquet`
- `reports/historical_summary.csv`: raw observation counts by sensor/year/month.

**Caution:** USA country CSV selection depends on the actual ZIP member naming. If the inventory reports zero USA files, inspect `example_members` and adapt the filename matcher before running extraction. This stage does not yet assign state boundaries, resolve duplicate observations, or harmonize sensors. Keep original ZIPs as the source of truth. Do not commit datasets to Git.

## Optional API skeleton
```powershell
uvicorn firescope.presentation.api.main:app --reload
```
Health check: `/health`. Other endpoints intentionally return HTTP 501 until implemented.

## GitHub upload (run at project root)
```powershell
git init
git remote add origin https://github.com/Ljara20/FireScopeAI.git
git add .
git commit -m "feat: bootstrap FireScope AI data foundation"
git branch -M main
git push -u origin main
```
If the remote is already configured, skip `git remote add`. If the remote has commits, pull/reconcile first.

## Design
Clean Architecture: domain → application ports/use cases → infrastructure adapters → API. Data processing is independent of web UI. See `docs/DATA_CONTRACT.md` and `docs/ROADMAP.md`.
