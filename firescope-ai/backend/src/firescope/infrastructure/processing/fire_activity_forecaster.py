"""One-month-ahead, sensor-specific retrospective forecasting with a fixed 2024-25 holdout.

Predicts *observed satellite detection counts*, never fires or risk. Training uses
only <=2023 rows. No current-month target, FRP or anomaly score is a predictor.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import Ridge


class FireActivityForecaster:
    REQUIRED = {'state_code', 'sensor', 'year', 'month', 'detection_count',
                'lag_1_month_detections', 'historical_mean', 'baseline_years',
                'month_sin', 'month_cos', 'has_consecutive_previous_month'}

    def __init__(self, source: Path, holdout_start: int = 2024, holdout_end: int = 2025,
                 minimum_train_rows: int = 30):
        self.source = Path(source)
        if holdout_start > holdout_end or minimum_train_rows < 2:
            raise ValueError('Invalid holdout range or minimum training rows')
        self.holdout_start, self.holdout_end = holdout_start, holdout_end
        self.minimum_train_rows = minimum_train_rows

    @staticmethod
    def _eligible(row: dict) -> bool:
        return (row['state_code'] is not None
                and row['lag_1_month_detections'] is not None
                and row['historical_mean'] is not None
                and row['historical_mean'] >= 0
                and row['baseline_years'] is not None
                and row['baseline_years'] >= 3
                and row['has_consecutive_previous_month'] is True)

    @staticmethod
    def _features(row: dict) -> dict:
        return {'state=' + str(row['state_code']): 1.0,
                'log_previous': float(np.log1p(row['lag_1_month_detections'])),
                'log_seasonal': float(np.log1p(row['historical_mean'])),
                'month_sin': float(row['month_sin']),
                'month_cos': float(row['month_cos']),
                'baseline_years': float(min(row['baseline_years'], 30))}

    @staticmethod
    def _mae(a, b) -> float:
        return float(np.mean(np.abs(np.asarray(a) - np.asarray(b))))

    def run(self, destination: Path, manifest: Path) -> dict[str, Any]:
        destination, manifest = Path(destination), Path(manifest)
        if len({self.source.resolve(), destination.resolve(), manifest.resolve()}) != 3:
            raise ValueError('Source, destination and manifest must differ')
        if not self.source.is_file():
            raise FileNotFoundError(self.source)
        table = pq.read_table(self.source)
        missing = sorted(self.REQUIRED - set(table.column_names))
        if missing:
            raise ValueError(f'Missing required columns: {missing}')
        rows = table.to_pylist()
        keys = set()
        for row in rows:
            key = (row['state_code'], row['sensor'], row['year'], row['month'])
            if key in keys:
                raise ValueError(f'Duplicate state/sensor/year/month key: {key}')
            keys.add(key)
            if (row['sensor'] is None or row['year'] is None or row['month'] is None
                or not 1 <= row['month'] <= 12 or row['detection_count'] is None
                or row['detection_count'] < 0):
                raise ValueError('Invalid source row')
        predictions: list[float | None] = [None] * len(rows)
        statuses = ['not_holdout' if not self.holdout_start <= r['year'] <= self.holdout_end
                    else 'insufficient_features' for r in rows]
        results: dict[str, Any] = {}
        for sensor in sorted({r['sensor'] for r in rows}):
            train = [i for i, r in enumerate(rows) if r['sensor'] == sensor
                     and r['year'] < self.holdout_start and self._eligible(r)]
            test = [i for i, r in enumerate(rows) if r['sensor'] == sensor
                    and self.holdout_start <= r['year'] <= self.holdout_end
                    and self._eligible(r)]
            result: dict[str, Any] = {'train_rows': len(train), 'holdout_rows': len(test),
                                      'holdout_years': [self.holdout_start, self.holdout_end]}
            if len(train) < self.minimum_train_rows or not test:
                result.update({'approved': False, 'reason': 'insufficient_train_or_holdout'})
                results[sensor] = result
                continue
            vec = DictVectorizer(sparse=True)
            x_train = vec.fit_transform([self._features(rows[i]) for i in train])
            y_train = np.log1p([rows[i]['detection_count'] for i in train])
            model = Ridge(alpha=10.0)
            model.fit(x_train, y_train)
            x_test = vec.transform([self._features(rows[i]) for i in test])
            model_log = np.maximum(0, model.predict(x_test))
            baseline_log = np.log1p([rows[i]['historical_mean'] for i in test])
            actual_log = np.log1p([rows[i]['detection_count'] for i in test])
            model_mae = self._mae(actual_log, model_log)
            baseline_mae = self._mae(actual_log, baseline_log)
            approved = bool(np.isfinite(model_mae) and model_mae < baseline_mae)
            selected = model_log if approved else baseline_log
            for i, prediction in zip(test, selected):
                predictions[i] = float(np.expm1(np.clip(prediction, 0, 30)))
                statuses[i] = 'model_validated' if approved else 'seasonal_baseline_fallback'
            result.update({'approved': approved, 'reason': 'beats_seasonal_baseline' if approved
                           else 'seasonal_baseline_preferred', 'model_log_mae': model_mae,
                           'baseline_log_mae': baseline_mae,
                           'relative_improvement': float((baseline_mae - model_mae) / baseline_mae)
                           if baseline_mae > 0 else None,
                           'selected_method': 'ridge_log1p' if approved else 'historical_mean'})
            results[sensor] = result
        out = table.append_column('forecast_detection_count', pa.array(predictions, type=pa.float64()))
        out = out.append_column('forecast_status', pa.array(statuses, type=pa.string()))
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
                  'forecast_rows': sum(p is not None for p in predictions),
                  'status_counts': {s: statuses.count(s) for s in sorted(set(statuses))},
                  'sensor_results': results,
                  'method': 'Per-sensor ridge regression on log1p counts, fixed pre-holdout training; seasonal baseline fallback',
                  'limitations': [
                      'Retrospective one-month-ahead evaluation, not a deployed future forecast.',
                      'Predictions only for 2024-2025 rows with prior-month observation and >=3 prior observed years.',
                      'No missing months are filled with zeros; no unobserved future rows are generated.',
                      'Holdout evaluation chooses between ridge and seasonal baseline on the same holdout: reported performance is selection-biased.',
                      'Observed satellite detections are not unique fires, burned area, severity, or fire probability.',
                      'No orbital coverage correction or cross-sensor pooling; one model per sensor.',
                      'Lag uses observed previous-month counts, so this is a one-step rolling-origin scenario.'
                  ]}
        manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return report
