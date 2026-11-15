"""Assign US state polygons and H3 cells without altering source observations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import geopandas as gpd
import h3
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import STRtree, Point


class SpatialProcessor:
    """Chunked enrichment; preserves row order, columns, and unassigned points."""

    REQUIRED = {"latitude_normalized", "longitude_normalized", "coordinates_status"}

    def __init__(self, source: Path, states_file: Path, resolution: int = 5, batch_size: int = 50_000):
        self.source = Path(source)
        self.states_file = Path(states_file)
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        if not self.states_file.is_file():
            raise FileNotFoundError(self.states_file)
        if not 0 <= resolution <= 15:
            raise ValueError("H3 resolution must be between 0 and 15")
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        self.resolution = resolution
        self.batch_size = batch_size

    def _states(self):
        frame = gpd.read_file(self.states_file)
        if frame.crs is None:
            raise ValueError("State polygons must declare their coordinate reference system")
        frame = frame.to_crs("EPSG:4326")
        code_col = next((c for c in ("STUSPS", "state_code") if c in frame.columns), None)
        name_col = next((c for c in ("NAME", "state_name") if c in frame.columns), None)
        if not code_col or not name_col:
            raise ValueError("State polygons need STUSPS/NAME (or state_code/state_name)")
        records = []
        for _, row in frame.iterrows():
            geom = row.geometry
            if geom is not None and not geom.is_empty:
                records.append((geom, str(row[code_col]), str(row[name_col])))
        if not records:
            raise ValueError("No valid state polygons")
        geometries = [r[0] for r in records]
        return STRtree(geometries), records

    def run(self, destination: Path, manifest: Path) -> dict[str, Any]:
        destination, manifest = Path(destination), Path(manifest)
        if destination.resolve() == self.source.resolve():
            raise ValueError("Output must not overwrite input")
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        tree, states = self._states()
        con = duckdb.connect()
        tmp = destination.with_name(destination.name + ".tmp.parquet")
        writer = None
        counts = {"assigned": 0, "outside_state_polygons": 0, "invalid_coordinates": 0}
        total = 0
        try:
            # The Parquet reader streams Arrow record batches instead of loading the dataset into RAM.
            columns = {r[0] for r in con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(self.source)]).fetchall()}
            missing = sorted(self.REQUIRED - columns)
            if missing:
                raise ValueError(f"Missing required columns: {missing}")
            extra = {"state_code", "state_name", "h3_cell_id", "spatial_status"}
            if columns & extra:
                raise ValueError(f"Output columns already exist: {sorted(columns & extra)}")
            reader = pq.ParquetFile(self.source)
            schema = reader.schema_arrow.append(pa.field("state_code", pa.string()))
            schema = schema.append(pa.field("state_name", pa.string()))
            schema = schema.append(pa.field("h3_cell_id", pa.string()))
            schema = schema.append(pa.field("spatial_status", pa.string()))
            writer = pq.ParquetWriter(tmp, schema, compression="zstd")
            for batch in reader.iter_batches(batch_size=self.batch_size):
                latitudes = batch.column(batch.schema.get_field_index("latitude_normalized")).to_pylist()
                longitudes = batch.column(batch.schema.get_field_index("longitude_normalized")).to_pylist()
                statuses = batch.column(batch.schema.get_field_index("coordinates_status")).to_pylist()
                codes, names, cells, spatial = [], [], [], []
                for lat, lon, status in zip(latitudes, longitudes, statuses):
                    code = name = cell = None
                    if status != "valid" or lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
                        result = "invalid_coordinates"
                    else:
                        cell = h3.latlng_to_cell(float(lat), float(lon), self.resolution)
                        point = Point(float(lon), float(lat))
                        # STRtree query uses bounding boxes; covers() includes boundary points.
                        matches = [states[int(i)] for i in tree.query(point) if states[int(i)][0].covers(point)]
                        if matches:
                            # Deterministic for rare points lying exactly on shared state boundaries.
                            _, code, name = min(matches, key=lambda item: item[1])
                            result = "assigned"
                        else:
                            result = "outside_state_polygons"
                    counts[result] += 1
                    codes.append(code)
                    names.append(name)
                    cells.append(cell)
                    spatial.append(result)
                augmented = pa.RecordBatch.from_arrays(
                    list(batch.columns) + [pa.array(codes, type=pa.string()),
                                           pa.array(names, type=pa.string()),
                                           pa.array(cells, type=pa.string()),
                                           pa.array(spatial, type=pa.string())],
                    schema=schema,
                )
                writer.write_batch(augmented)
                total += batch.num_rows
            writer.close()
            writer = None
            tmp.replace(destination)
            result = {"input": str(self.source), "output": str(destination),
                      "states_file": str(self.states_file), "h3_resolution": self.resolution,
                      "total_observations": total, "spatial_status_counts": counts,
                      "notes": ["All input rows and columns retained.",
                                "H3 cells are geographic bins, not fire events.",
                                "Points outside state polygons are retained, including offshore points.",
                                "State boundaries are from the supplied geometry file."]}
            manifest.write_text(json.dumps(result, indent=2), encoding="utf-8")
            return result
        finally:
            if writer is not None:
                writer.close()
            tmp.unlink(missing_ok=True)
            con.close()
