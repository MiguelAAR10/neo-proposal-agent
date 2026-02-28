import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from qdrant_client import QdrantClient

sys.path.append(str(Path(__file__).parent.parent / "backend"))
from src.config import get_settings  # noqa: E402


def classify_status(url: str, timeout: float) -> tuple[str, int | None, str | None]:
    try:
        resp = requests.head(url, allow_redirects=True, timeout=timeout)
        if resp.status_code == 405:
            resp = requests.get(url, allow_redirects=True, timeout=timeout)

        if 200 <= resp.status_code < 400:
            return "verified", resp.status_code, None
        return "inaccessible", resp.status_code, None
    except requests.RequestException as exc:
        return "unknown", None, str(exc)


def main(limit: int, timeout: float) -> int:
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)

    points, _ = client.scroll(
        collection_name=settings.qdrant_collection_cases,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    updates = []
    now = datetime.now(timezone.utc).isoformat()

    for p in points:
        payload = dict(p.payload or {})
        url = payload.get("url_slide")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            payload["link_status"] = "unknown"
            payload["last_checked_at"] = now
            payload["check_error"] = "invalid_url"
        else:
            status, code, error = classify_status(url, timeout)
            payload["link_status"] = status
            payload["last_checked_at"] = now
            payload["check_error"] = error
            if code is not None:
                payload["last_http_status"] = code

        updates.append((p.id, payload))

    if updates:
        for point_id, payload in updates:
            client.set_payload(
                collection_name=settings.qdrant_collection_cases,
                payload=payload,
                points=[point_id],
            )

    print(f"Checked {len(updates)} case links.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate case URLs and update link_status in Qdrant.")
    parser.add_argument("--limit", type=int, default=200, help="Max points to check")
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout seconds")
    args = parser.parse_args()
    raise SystemExit(main(limit=args.limit, timeout=args.timeout))
