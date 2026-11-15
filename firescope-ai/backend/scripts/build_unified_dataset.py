"""
Unify NASA FIRMS sensor schemas and generate historical reports.

IMPORTANT:
This process performs schema unification, NOT scientific harmonization.
MODIS and VIIRS observations remain identifiable by their source sensor.
"""

import argparse
from pathlib import Path

import duckdb

from _bootstrap import DATA, REPORTS


def build_parquet_file_list(files: list[Path]) -> str:
    """
    Build a SQL-compatible list of Parquet file paths.

    DuckDB does not support prepared parameters inside CREATE VIEW
    statements, so file paths must be provided as SQL literals.
    """
    escaped_paths = [
        f"'{str(path).replace(chr(39), chr(39) * 2)}'"
        for path in files
    ]

    return f"[{', '.join(escaped_paths)}]"


def main() -> None:
    """Build the unified USA dataset and historical summary."""

    parser = argparse.ArgumentParser(
        description="Unify NASA FIRMS MODIS and VIIRS datasets."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DATA / "processed",
        help="Directory containing sensor-specific Parquet files.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DATA / "processed" / "firescope_usa_unified.parquet",
        help="Output path for the unified dataset.",
    )

    args = parser.parse_args()

    # --------------------------------------------------
    # 1. Discover sensor-specific Parquet files
    # --------------------------------------------------

    files = sorted(
        path
        for path in args.input.glob("*_usa.parquet")
        if path.resolve() != args.output.resolve()
    )

    if not files:
        raise SystemExit(
            "No sensor Parquet found. "
            "Run extract_usa_data.py first."
        )

    print("\nFireScope AI - Unified Dataset Builder")
    print("=" * 50)

    for file in files:
        print(f"Input: {file.name}")

    # --------------------------------------------------
    # 2. Initialize DuckDB
    # --------------------------------------------------

    con = duckdb.connect()

    try:
        con.execute("SET preserve_insertion_order=false")

        # --------------------------------------------------
        # 3. Create unified view
        # --------------------------------------------------

        parquet_list = build_parquet_file_list(files)

        con.execute(
            f"""
            CREATE OR REPLACE TEMP VIEW unified AS
            SELECT *
            FROM read_parquet(
                {parquet_list},
                union_by_name=true
            )
            """
        )

        # --------------------------------------------------
        # 4. Export unified dataset
        # --------------------------------------------------

        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = str(args.output).replace("'", "''")

        con.execute(
            f"""
            COPY (
                SELECT *
                FROM unified
            )
            TO '{output_path}'
            (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """
        )

        # --------------------------------------------------
        # 5. Generate historical report
        # --------------------------------------------------

        REPORTS.mkdir(
            parents=True,
            exist_ok=True,
        )

        summary = REPORTS / "historical_summary.csv"

        summary_path = str(summary).replace("'", "''")

        con.execute(
            f"""
            COPY (
                SELECT
                    source_sensor,

                    date_part(
                        'year',
                        TRY_CAST(acq_date AS DATE)
                    )::INTEGER AS year,

                    date_part(
                        'month',
                        TRY_CAST(acq_date AS DATE)
                    )::INTEGER AS month,

                    COUNT(*) AS raw_hotspot_observations,

                    COUNT_IF(
                        TRY_CAST(frp AS DOUBLE) IS NOT NULL
                    ) AS records_with_frp

                FROM unified

                GROUP BY 1, 2, 3

                ORDER BY 1, 2, 3
            )
            TO '{summary_path}'
            (
                HEADER,
                DELIMITER ','
            )
            """
        )

        # --------------------------------------------------
        # 6. Display results
        # --------------------------------------------------

        total_records = con.execute(
            "SELECT COUNT(*) FROM unified"
        ).fetchone()[0]

        print("\n" + "=" * 50)
        print("PROCESSING COMPLETED")
        print("=" * 50)

        print(f"Total observations: {total_records:,}")
        print(f"Unified dataset: {args.output}")
        print(f"Historical summary: {summary}")

        print(
            "\nNOTE: These are raw satellite observations, "
            "not scientifically harmonized fire counts."
        )

    finally:
        con.close()


if __name__ == "__main__":
    main()