import sys
from pathlib import Path
import pytest

def _engineer():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'src'))
    from firescope.infrastructure.processing.feature_engineer import FeatureEngineer
    return FeatureEngineer


def _fixture(path):
    import duckdb
    con = duckdb.connect()
    con.execute(f'''COPY (
      SELECT 'CA'::VARCHAR AS state_code, 'California'::VARCHAR AS state_name,
             'modis'::VARCHAR AS sensor, y::INTEGER AS year, 7::INTEGER AS month,
             (y-2019)::BIGINT AS detection_count, 1::INTEGER AS days_with_detections,
             10.0::DOUBLE AS frp_sum_mw,
             1.0::DOUBLE AS median_daily_cell_aligned_log_activity,
             'reference'::VARCHAR AS alignment_status
      FROM range(2020, 2025) t(y)
      UNION ALL
      SELECT 'CA', 'California', 'viirs_snpp', 2024, 7, 50, 1, 10.0, 1.0,
             'validated_exploratory'
    ) TO '{str(path).replace("'", "''")}' (FORMAT PARQUET)''')
    con.close()


def test_features_preserve_rows_and_avoid_future_leakage(tmp_path):
    import duckdb
    source, dest, manifest = (tmp_path / p for p in ('input.parquet', 'out.parquet', 'manifest.json'))
    _fixture(source)
    result = _engineer()(source).run(dest, manifest)
    assert result['input_rows'] == result['output_rows'] == 6
    assert result['detections_preserved'] == 65
    con = duckdb.connect()
    rows = con.execute(f"SELECT year, baseline_years, historical_mean, has_minimum_baseline, lag_1_month_detections FROM read_parquet('{dest}') WHERE sensor='modis' ORDER BY year").fetchall()
    assert [r[1] for r in rows] == [0, 1, 2, 3, 4]
    assert rows[3][2] == 2.0  # only 2020, 2021, 2022
    assert rows[3][3] is True
    assert all(r[4] is None for r in rows)  # July is not consecutive to previous July
    assert con.execute(f"SELECT count(*) FROM read_parquet('{dest}') WHERE sensor='viirs_snpp' AND baseline_years=0").fetchone()[0] == 1
    con.close()


def test_missing_columns(tmp_path):
    import duckdb
    src = tmp_path / 'bad.parquet'
    duckdb.connect().execute(f"COPY (SELECT 1 AS arbitrary) TO '{src}' (FORMAT PARQUET)")
    with pytest.raises(ValueError, match='Missing required columns'):
        _engineer()(src).run(tmp_path / 'out.parquet', tmp_path / 'manifest.json')


def test_prevent_overwrite(tmp_path):
    src = tmp_path / 'input.parquet'
    src.touch()
    with pytest.raises(ValueError, match='must differ'):
        _engineer()(src).run(src, tmp_path / 'manifest.json')
