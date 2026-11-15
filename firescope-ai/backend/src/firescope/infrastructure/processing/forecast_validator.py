"""Independent temporal evaluation of per-sensor one-month satellite-detection forecasts.

Train <=2021, select on 2022-23, refit selected Ridge through 2023,
then evaluate once on untouched 2024-25. No cross-sensor pooling.
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import Ridge
from firescope.infrastructure.processing.fire_activity_forecaster import FireActivityForecaster


class ForecastValidator:
    REQUIRED = FireActivityForecaster.REQUIRED

    def __init__(self, source: Path, selection_start: int = 2022,
                 test_start: int = 2024, test_end: int = 2025,
                 minimum_train_rows: int = 30, minimum_selection_rows: int = 20):
        self.source = Path(source)
        if not selection_start < test_start <= test_end or min(minimum_train_rows, minimum_selection_rows) < 2:
            raise ValueError('Invalid temporal split or minimum rows')
        self.selection_start, self.test_start, self.test_end = selection_start, test_start, test_end
        self.minimum_train_rows, self.minimum_selection_rows = minimum_train_rows, minimum_selection_rows

    @staticmethod
    def _fit(rows, indices):
        vec = DictVectorizer(sparse=True)
        x = vec.fit_transform([FireActivityForecaster._features(rows[i]) for i in indices])
        y = np.log1p([rows[i]['detection_count'] for i in indices])
        model = Ridge(alpha=10.0).fit(x, y)
        return vec, model

    @staticmethod
    def _predict(rows, indices, vec, model):
        x = vec.transform([FireActivityForecaster._features(rows[i]) for i in indices])
        return np.maximum(0.0, model.predict(x))

    @staticmethod
    def _metrics(rows, indices, prediction_log):
        if not indices:
            return None
        actual = np.log1p(np.array([rows[i]['detection_count'] for i in indices], dtype=float))
        baseline = np.log1p(np.array([rows[i]['historical_mean'] for i in indices], dtype=float))
        prediction_log = np.asarray(prediction_log, dtype=float)
        model_mae = float(np.mean(np.abs(actual - prediction_log)))
        base_mae = float(np.mean(np.abs(actual - baseline)))
        return {'rows': len(indices), 'selected_log_mae': model_mae,
                'baseline_log_mae': base_mae,
                'relative_improvement': float((base_mae-model_mae)/base_mae) if base_mae > 0 else None}

    def run(self, destination: Path, manifest: Path) -> dict:
        destination, manifest = Path(destination), Path(manifest)
        if len({self.source.resolve(), destination.resolve(), manifest.resolve()}) != 3:
            raise ValueError('Input, output and manifest paths must differ')
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        table = pq.read_table(self.source)
        missing = sorted(self.REQUIRED - set(table.column_names))
        if missing:
            raise ValueError(f'Missing required columns: {missing}')
        rows = table.to_pylist()
        seen = set()
        for r in rows:
            key = (r['state_code'], r['sensor'], r['year'], r['month'])
            if key in seen:
                raise ValueError(f'Duplicate monthly key: {key}')
            seen.add(key)
            if r['sensor'] is None or r['year'] is None or r['month'] is None or not 1 <= r['month'] <= 12 or r['detection_count'] is None or r['detection_count'] < 0:
                raise ValueError('Invalid source row')
        preds = [None] * len(rows)
        statuses = ['outside_test' if not self.test_start <= r['year'] <= self.test_end else 'insufficient_features' for r in rows]
        results = {}
        for sensor in sorted({r['sensor'] for r in rows}):
            eligible = lambda i: rows[i]['sensor'] == sensor and FireActivityForecaster._eligible(rows[i])
            train = [i for i in range(len(rows)) if eligible(i) and rows[i]['year'] < self.selection_start]
            selection = [i for i in range(len(rows)) if eligible(i) and self.selection_start <= rows[i]['year'] < self.test_start]
            test = [i for i in range(len(rows)) if eligible(i) and self.test_start <= rows[i]['year'] <= self.test_end]
            result = {'train_rows': len(train), 'selection_rows': len(selection), 'test_rows': len(test)}
            if len(train) < self.minimum_train_rows or len(selection) < self.minimum_selection_rows or not test:
                result.update({'selected_method': None, 'reason': 'insufficient_split_data', 'independent_test': None})
                results[sensor] = result
                continue
            vec, model = self._fit(rows, train)
            ridge_selection = self._predict(rows, selection, vec, model)
            selection_actual = np.log1p([rows[i]['detection_count'] for i in selection])
            selection_baseline = np.log1p([rows[i]['historical_mean'] for i in selection])
            ridge_mae = float(np.mean(np.abs(selection_actual - ridge_selection)))
            baseline_mae = float(np.mean(np.abs(selection_actual - selection_baseline)))
            use_ridge = bool(np.isfinite(ridge_mae) and ridge_mae < baseline_mae)
            method = 'ridge_log1p' if use_ridge else 'historical_mean'
            if use_ridge:
                # Refit only with pre-test observations; test years are never used for selection or fitting.
                refit = train + selection
                vec, model = self._fit(rows, refit)
                test_log = self._predict(rows, test, vec, model)
            else:
                test_log = np.log1p([rows[i]['historical_mean'] for i in test])
            test_metrics = self._metrics(rows, test, test_log)
            for i, logp in zip(test, test_log):
                preds[i] = float(np.expm1(np.clip(logp, 0, 30)))
                statuses[i] = 'independent_test_prediction'
            by_state = {}
            for state in sorted({rows[i]['state_code'] for i in test}):
                indices = [j for j, i in enumerate(test) if rows[i]['state_code'] == state]
                subset = [test[j] for j in indices]
                by_state[state] = self._metrics(rows, subset, [test_log[j] for j in indices])
            result.update({'selected_method': method, 'reason': 'selection_period_only',
                           'selection_ridge_log_mae': ridge_mae,
                           'selection_baseline_log_mae': baseline_mae,
                           'independent_test': test_metrics,
                           'test_by_state': by_state,
                           'independent_test_beats_baseline': bool(test_metrics['relative_improvement'] is not None and test_metrics['relative_improvement'] > 0)})
            results[sensor] = result
        out = table.append_column('independent_forecast_detection_count', pa.array(preds, type=pa.float64()))
        out = out.append_column('independent_forecast_status', pa.array(statuses, type=pa.string()))
        destination.parent.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        tmp = destination.with_name(destination.name + '.tmp.parquet')
        try:
            pq.write_table(out, tmp, compression='zstd')
            tmp.replace(destination)
        finally:
            tmp.unlink(missing_ok=True)
        report = {'input': str(self.source.resolve()), 'output': str(destination.resolve()),
                  'input_rows': len(rows), 'output_rows': out.num_rows,
                  'detections_preserved': int(sum(r['detection_count'] for r in rows)),
                  'independent_test_predictions': sum(p is not None for p in preds),
                  'status_counts': dict(Counter(statuses)),
                  'split': {'train_before': self.selection_start, 'selection_years': list(range(self.selection_start, self.test_start)),
                            'test_years': list(range(self.test_start, self.test_end + 1))},
                  'sensor_results': results,
                  'method': 'Select Ridge versus seasonal mean on 2022-23; refit Ridge through 2023 if selected; evaluate once on untouched 2024-25.',
                  'limitations': ['Independent temporal test is still retrospective, not an operational future forecast.',
                                  'Test-year historical_mean and lag must be available before the target month; audit upstream feature generation for temporal leakage.',
                                  'No missing months imputed; predictions are conditional on observed months and available prior features.',
                                  'No orbital-coverage correction; sensor counts do not measure individual fires or risk.',
                                  'Single temporal test block; no uncertainty intervals or statistical significance test.']}
        manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return report
