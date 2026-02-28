from __future__ import annotations

import argparse
import json

from src.tools.qdrant_tool import db_connection


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verifica links de casos y actualiza link_status en Qdrant."
    )
    parser.add_argument(
        "--collection",
        default="neo_cases_v1",
        help="Nombre de coleccion en Qdrant (default: neo_cases_v1)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Tamaño de lote para scroll/update (default: 64)",
    )
    args = parser.parse_args()

    summary = db_connection.verify_links_status(
        collection_name=args.collection,
        batch_size=args.batch_size,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

