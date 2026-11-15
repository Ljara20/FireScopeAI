from pathlib import Path
import json

import duckdb
import pyarrow.parquet as pq
import pytest

from firescope.infrastructure.processing.spatial_processor import SpatialProcessor


def _fixture(tmp_path: Path):
    # Small synthetic polygon; no network required for tests.
    geojson = tmp_path / "states.geojson"
    geojson.write_text(json.dumps({"type": "FeatureCollection", "features": [{
        "type": "Feature", "properties": {"STUSPS": "TS", "NAME": "Test State"},
        "geometry": {"type": "Polygon", "coordinates": [[[-101, 39], [-99, 39], [-99, 41], [-101, 41], [-101, 39]]]}
    }]}), encoding="utf-8")
    source = tmp_path / "normalized.parquet"
    con = duckdb.connect()
    con.execute("""COPY (SELECT * FROM (VALUES
      (40.0, -100.0, 'valid', 'modis'),
      (42.0, -100.0, 'valid', 'viirs_snpp'),
      (NULL, -100.0, 'invalid', 'modis')
    ) AS t(latitude_normalized, longitude_normalized, coordinates_status, source_sensor))
    TO ? (FORMAT PARQUET)""", [str(source)])
    con.close()
    return source, geojson


def test_assign_preserves_rows_and_labels(tmp_path):
    source, states = _fixture(tmp_path)
    output, report = tmp_path / "out.parquet", tmp_path / "report.json"
    result = SpatialProcessor(source, states, resolution=5, batch_size=2).run(output, report)
    assert result["total_observations"] == 3
    assert result["spatial_status_counts"] == {"assigned": 1, "outside_state_polygons": 1, "invalid_coordinates": 1}
    table = pq.read_table(output)
    assert table.num_rows == 3
    assert table["state_code"].to_pylist() == ["TS", None, None]
    assert table["spatial_status"].to_pylist() == ["assigned", "outside_state_polygons", "invalid_coordinates"]
    assert table["h3_cell_id"].to_pylist()[0] is not None
    assert table["h3_cell_id"].to_pylist()[1] is not None
    assert table["h3_cell_id"].to_pylist()[2] is None
    assert "source_sensor" in table.column_names
    assert report.exists()


def test_reject_overwrite(tmp_path):
    source, states = _fixture(tmp_path)
    with pytest.raises(ValueError, match="overwrite"):
        SpatialProcessor(source, states).run(source, tmp_path / "report.json")


def test_missing_columns(tmp_path):
    _, states = _fixture(tmp_path)
    source = tmp_path / "bad.parquet"
    con = duckdb.connect()
    con.execute("COPY (SELECT 1 AS latitude_normalized) TO ? (FORMAT PARQUET)", [str(source)])
    con.close()
    with pytest.raises(ValueError, match="Missing required columns"):
        SpatialProcessor(source, states).run(tmp_path / "out.parquet", tmp_path / "report.json")
