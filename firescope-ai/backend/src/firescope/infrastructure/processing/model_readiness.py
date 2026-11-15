"""Phase 3.5: auditable scientific handoff, not model training or future forecasting."""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import math
import pyarrow.parquet as pq


class ModelReadiness:
    REQUIRED = {'state_code', 'sensor', 'year', 'month', 'detection_count',
                'historical_mean', 'independent_forecast_detection_count',
                'independent_forecast_status'}

    def __init__(self, source: Path, validation_manifest: Path):
        self.source = Path(source)
        self.validation_manifest = Path(validation_manifest)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _metrics(records):
        n = len(records)
        if not n:
            return None
        model = sum(abs(math.log1p(a) - math.log1p(p)) for a, p, _ in records) / n
        baseline = sum(abs(math.log1p(a) - math.log1p(b)) for a, _, b in records) / n
        return {'rows': n, 'model_log_mae': model, 'baseline_log_mae': baseline,
                'relative_improvement': (baseline - model) / baseline if baseline > 0 else None}

    def run(self, destination: Path) -> dict:
        destination = Path(destination)
        if destination.resolve() in {self.source.resolve(), self.validation_manifest.resolve()}:
            raise ValueError('Output must differ from inputs')
        manifest = json.loads(self.validation_manifest.read_text(encoding='utf-8'))
        split = manifest['split']
        test_years = set(split['test_years'])
        if set(split['selection_years']) & test_years or any(y >= min(test_years) for y in split['selection_years']):
            raise ValueError('Overlapping or invalid selection/test periods')
        table = pq.read_table(self.source)
        missing = self.REQUIRED - set(table.column_names)
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')
        if table.num_rows != manifest['output_rows']:
            raise ValueError('Row conservation mismatch')
        groups = defaultdict(list)
        by_sensor = defaultdict(list)
        seen = set()
        total = 0
        predicted = 0
        for row in table.to_pylist():
            key = (row['state_code'], row['sensor'], row['year'], row['month'])
            if key in seen:
                raise ValueError('Duplicate monthly key')
            seen.add(key)
            actual = row['detection_count']
            if actual is None or actual < 0:
                raise ValueError('Invalid detection count')
            total += actual
            pred = row['independent_forecast_detection_count']
            status = row['independent_forecast_status']
            if pred is None:
                if status == 'independent_test_prediction':
                    raise ValueError('Prediction status without prediction')
                continue
            if row['year'] not in test_years or status != 'independent_test_prediction':
                raise ValueError('Prediction outside independent test')
            baseline = row['historical_mean']
            if baseline is None or not all(math.isfinite(float(x)) and x >= 0 for x in (pred, baseline)):
                raise ValueError('Invalid prediction or baseline')
            predicted += 1
            triple = (float(actual), float(pred), float(baseline))
            by_sensor[row['sensor']].append(triple)
            groups[(row['sensor'], row['year'], row['state_code'])].append(triple)
        if total != manifest['detections_preserved'] or predicted != manifest['independent_test_predictions']:
            raise ValueError('Detection or prediction conservation mismatch')
        sensors = {}
        for sensor, data in sorted(by_sensor.items()):
            reported = manifest['sensor_results'].get(sensor)
            if not reported or reported['test_rows'] != len(data):
                raise ValueError(f'Sensor test count mismatch: {sensor}')
            metrics = self._metrics(data)
            reported_mae = reported['independent_test']['selected_log_mae']
            if not math.isclose(metrics['model_log_mae'], reported_mae, rel_tol=1e-7, abs_tol=1e-8):
                raise ValueError(f'Manifest/parquet metric mismatch: {sensor}')
            years = {str(year): self._metrics([t for (s, y, _), items in groups.items() if s == sensor and y == year for t in items])
                     for year in sorted(test_years)}
            states = {state: self._metrics([t for (s, _, st), items in groups.items() if s == sensor and st == state for t in items])
                      for state in sorted({st for s, _, st in groups if s == sensor})}
            sensors[sensor] = {
                'selection_method': reported['selected_method'],
                'independent_test': metrics,
                'by_year': years,
                'by_state': states,
                'model_beats_baseline_on_test': metrics['relative_improvement'] is not None and metrics['relative_improvement'] > 0,
                'display_policy': 'experimental_retrospective_only',
            }
        report = {
            'schema_version': '1.0.0', 'release_gate': 'historical_analytics_only',
            'input': str(self.source.resolve()),
            'source_sha256': self._sha256(self.source),
            'validation_manifest_sha256': self._sha256(self.validation_manifest),
            'row_count': table.num_rows, 'detections_preserved': total,
            'independent_test_predictions': predicted, 'split': split,
            'sensor_results': sensors,
            'display_policy': {
                'allowed': ['historical_satellite_detections', 'seasonal_climatology', 'retrospective_anomalies', 'experimental_retrospective_model_evaluation'],
                'prohibited': ['operational_early_warning', 'wildfire_probability', 'predicted_unique_fires', 'validated_future_forecast'],
            },
            'release_checks': {
                'row_and_detection_conservation': 'passed',
                'temporal_split_disjoint': 'passed',
                'predictions_restricted_to_test_years': 'passed',
                'forecast_origin_feature_availability': 'not_verified_requires_upstream_lineage_audit',
                'orbital_coverage_correction': 'not_implemented',
                'operational_forecast_readiness': 'not_approved',
            },
            'limitations': [
                'Satellite detections are not unique fires, severity, burned area or risk.',
                'Test observations may depend on prior observed months; operational availability is not established.',
                'No proof that every upstream historical feature was available at its forecast origin.',
                'No statistical significance or calibrated uncertainty claimed.',
                'No cross-sensor equivalence or orbital coverage correction established.',
            ],
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_name(destination.name + '.tmp')
        try:
            tmp.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
            tmp.replace(destination)
        finally:
            tmp.unlink(missing_ok=True)
        return report
