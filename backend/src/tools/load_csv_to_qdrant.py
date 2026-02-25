from pathlib import Path

from src.tools.qdrant_tool import db_connection


def main() -> None:
    base = Path("data")
    csv_files = sorted(str(p) for p in base.glob("*.csv"))
    if not csv_files:
        raise SystemExit("No se encontraron CSV en ./data")

    inserted = db_connection.load_csv_files(csv_files, collection_name="neo_cases_v1")
    print(f"CSV procesados: {len(csv_files)}")
    print(f"Registros cargados en neo_cases_v1: {inserted}")


if __name__ == "__main__":
    main()
