"""Run from backend/: python3 scripts/detect_fire_anomalies.py"""
from pathlib import Path
import sys
BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND / 'src'))
from firescope.application.use_cases.detect_fire_anomalies import DetectFireAnomalies

def main():
    report = DetectFireAnomalies().execute(
        ROOT / 'data/processed/firescope_usa_fire_features.parquet',
        ROOT / 'data/processed/firescope_usa_fire_anomalies.parquet',
        ROOT / 'reports/data_quality/fire_anomalies_manifest.json',
    )
    print(f"Input rows: {report['input_rows']:,}")
    print(f"Output rows: {report['output_rows']:,}")
    print(f"Detections preserved: {report['detections_preserved']:,}")
    for label, count in sorted(report['anomaly_classes'].items()):
        print(f'{label}: {count:,}')
    print(f"Output: {report['output']}")

if __name__ == '__main__':
    main()
