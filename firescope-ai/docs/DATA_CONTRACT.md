# Stage 1 data contract

- Input: yearly NASA FIRMS ZIP archives with country CSV files; expected USA filename e.g. `United_States.csv`.
- Required CSV columns: `latitude`, `longitude`, `acq_date`.
- Output: one Parquet per sensor, plus a **schema-unified** Parquet.
- Source columns are retained as strings in stage 1 to avoid implicit cross-sensor conversions.
- Provenance: `source_sensor`, `source_archive`, `source_member`.
- Filters: valid latitude, longitude, parseable date. Country is determined by the supplied country CSV filename; not a coordinate bounding box.
- This does not de-duplicate overlapping sensors or calibrate different detection sensitivities.
- Raw monthly counts must not be interpreted as harmonized fire activity or unique fires.
- Archive naming and internal USA filename must be verified in the inventory before processing real data.
- Stage 2: validate schemas, scientific harmonization, spatial assignment to states/grid, coverage and missingness.
