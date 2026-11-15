"""Conservative, auditable MODIS/VIIRS activity alignment (not fire-count equivalence)."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import duckdb


class SensorHarmonizer:
    """Fit sensor-specific log-count alignment using co-observed H3/month pairs.

    Calibration is exploratory: co-detections are not independent fire events,
    and matching detections do not establish equal satellite coverage.
    """

    REQUIRED = {"activity_date", "sensor", "h3_cell_id", "detection_count"}
    SENSORS = ("modis", "viirs_snpp", "viirs_noaa20")

    def __init__(self, source: Path, reference: str = "modis", min_pairs: int = 100,
                 min_years: int = 3, min_improvement: float = 0.05):
        self.source = Path(source)
        self.reference = reference
        self.min_pairs = min_pairs
        self.min_years = min_years
        self.min_improvement = min_improvement
        if reference != "modis":
            raise ValueError("Only MODIS is supported as the reference sensor")

    @staticmethod
    def _quote(path: Path) -> str:
        return "'" + str(path.resolve()).replace("'", "''") + "'"

    def run(self, destination: Path, manifest: Path) -> dict[str, Any]:
        destination, manifest = Path(destination), Path(manifest)
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        if self.source.resolve() in (destination.resolve(), manifest.resolve()):
            raise ValueError("Cannot overwrite the input dataset")
        if destination.resolve() == manifest.resolve():
            raise ValueError("Output and manifest must be different files")
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        con = duckdb.connect()
        try:
            src = self._quote(self.source)
            columns = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet({src})").fetchall()}
            missing = self.REQUIRED - columns
            if missing:
                raise ValueError(f"Missing required columns: {sorted(missing)}")
            con.execute(f"CREATE TEMP VIEW observations AS SELECT * FROM read_parquet({src})")
            sensors = {r[0] for r in con.execute("SELECT DISTINCT sensor FROM observations").fetchall()}
            if not sensors.issubset(set(self.SENSORS)):
                raise ValueError(f"Unknown sensors: {sorted(sensors - set(self.SENSORS))}")
            bad = con.execute("""SELECT count(*) FROM observations WHERE detection_count IS NULL
                OR TRY_CAST(detection_count AS DOUBLE) < 0
                OR NOT isfinite(TRY_CAST(detection_count AS DOUBLE))""").fetchone()[0]
            if bad:
                raise ValueError(f"Invalid detection_count rows: {bad}")

            # Only months/cells with positive detections in BOTH sensors are matched.
            # This excludes zero-activity periods and does NOT measure true coverage.
            con.execute("""
                CREATE TEMP TABLE monthly AS
                SELECT sensor, h3_cell_id,
                       date_trunc('month', TRY_CAST(activity_date AS DATE))::DATE AS month,
                       SUM(detection_count)::DOUBLE AS n
                FROM observations
                WHERE h3_cell_id IS NOT NULL AND TRY_CAST(activity_date AS DATE) IS NOT NULL
                GROUP BY 1, 2, 3
            """)
            con.execute("""
                CREATE TEMP TABLE pairs AS
                SELECT v.sensor, v.month, v.h3_cell_id,
                       ln(1 + m.n) AS reference_log,
                       ln(1 + v.n) AS target_log
                FROM monthly v JOIN monthly m
                  ON v.month=m.month AND v.h3_cell_id=m.h3_cell_id
                WHERE m.sensor='modis' AND v.sensor <> 'modis'
                  AND m.n > 0 AND v.n > 0
            """)
            results: dict[str, Any] = {
                "modis": {"approved": True, "scale": 1.0, "reason": "reference"}
            }
            for sensor in ("viirs_snpp", "viirs_noaa20"):
                # Hold out the most recent TWO calendar years with paired detections.
                years = [r[0] for r in con.execute(
                    "SELECT DISTINCT year(month) FROM pairs WHERE sensor=? ORDER BY 1", [sensor]
                ).fetchall()]
                if len(years) < self.min_years:
                    results[sensor] = {"approved": False, "scale": None,
                                       "reason": "insufficient overlapping years", "overlap_years": years}
                    continue
                holdout = years[-2:]
                train = con.execute("""
                    SELECT count(*), median(reference_log / NULLIF(target_log, 0))
                    FROM pairs WHERE sensor=? AND year(month) NOT IN (?, ?)
                """, [sensor, *holdout]).fetchone()
                ntrain, scale = train
                if ntrain < self.min_pairs or scale is None or not math.isfinite(scale) or scale <= 0:
                    results[sensor] = {"approved": False, "scale": None,
                                       "reason": "insufficient or invalid training pairs",
                                       "train_pairs": ntrain, "holdout_years": holdout}
                    continue
                validation = con.execute("""
                    SELECT count(*), avg(abs(reference_log - target_log)),
                           avg(abs(reference_log - target_log * ?))
                    FROM pairs WHERE sensor=? AND year(month) IN (?, ?)
                """, [scale, sensor, *holdout]).fetchone()
                ntest, baseline_mae, adjusted_mae = validation
                improvement = ((baseline_mae - adjusted_mae) / baseline_mae
                               if baseline_mae and baseline_mae > 0 else 0.0)
                approved = bool(ntest >= max(20, self.min_pairs // 5)
                                and improvement >= self.min_improvement)
                results[sensor] = {
                    "approved": approved,
                    "scale": float(scale) if approved else None,
                    "candidate_scale": float(scale),
                    "train_pairs": ntrain, "validation_pairs": ntest,
                    "holdout_years": holdout,
                    "baseline_log_mae": baseline_mae,
                    "adjusted_log_mae": adjusted_mae,
                    "relative_improvement": improvement,
                    "reason": "validated exploratory alignment" if approved
                              else "validation threshold not met",
                }

            # An aligned activity proxy is derived ONLY for validated sensors.
            # The scale is applied to log(1 + daily count), not raw count or FRP.
            # Avoid inventing comparability where validation fails.
            clauses = ["WHEN sensor = 'modis' THEN ln(1 + detection_count)"]
            for sensor in ("viirs_snpp", "viirs_noaa20"):
                if results[sensor]["approved"]:
                    clauses.append(f"WHEN sensor = '{sensor}' THEN "
                                   f"ln(1 + detection_count) * {results[sensor]['scale']:.17g}")
            case_sql = "CASE " + " ".join(clauses) + " ELSE NULL END"
            out = self._quote(destination)
            con.execute(f"""
                COPY (
                    SELECT *, {case_sql}::DOUBLE AS aligned_log_activity,
                           CASE WHEN sensor='modis' THEN 'reference'
                                WHEN {case_sql} IS NOT NULL THEN 'validated_exploratory'
                                ELSE 'not_calibrated' END AS alignment_status
                    FROM observations
                ) TO {out} (FORMAT PARQUET, COMPRESSION ZSTD)
            """)
            source_rows = con.execute("SELECT count(*) FROM observations").fetchone()[0]
            output_rows = con.execute(f"SELECT count(*) FROM read_parquet({out})").fetchone()[0]
            if source_rows != output_rows:
                destination.unlink(missing_ok=True)
                raise RuntimeError("Row count mismatch after harmonization")
            report = {
                "input": str(self.source.resolve()), "output": str(destination.resolve()),
                "input_groups": source_rows, "output_groups": output_rows,
                "reference": self.reference, "sensor_results": results,
                "method": "median ratio of log1p monthly H3 matched positive detection counts; last two paired years held out",
                "limitations": [
                    "Exploratory alignment, not scientifically validated fire equivalence.",
                    "Matched positive months are not proof of equal satellite coverage.",
                    "No zero-detection days inferred; no FRP cross-sensor calibration.",
                    "Daily aligned_log_activity is a proxy, not a probability, fire count or severity.",
                    "Cross-sensor summation of aligned values is not justified."
                ],
            }
            manifest.write_text(json.dumps(report, indent=2), encoding="utf-8")
            return report
        finally:
            con.close()
