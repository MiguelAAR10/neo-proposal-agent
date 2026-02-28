from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Literal
from urllib.parse import urlparse

import redis
from src.config import get_settings
from src.services.errors import ExternalDependencyTimeout
from src.tools.qdrant_tool import db_connection

SwitchType = Literal["neo", "ai", "both"]
_EMBED_CACHE: dict[str, tuple[float, list[float]]] = {}
_EMBED_CACHE_TTL_SEC = 60 * 60 * 24
_EMBED_CACHE_MAX = 500
_REDIS_CACHE_PREFIX = "embed:v1:"
_REDIS_CLIENT: redis.Redis | None = None
_REDIS_UNAVAILABLE = False


def _normalized_query(query: str) -> str:
    return " ".join((query or "").strip().lower().split())


def _cache_key(query: str) -> str:
    digest = hashlib.sha1(_normalized_query(query).encode("utf-8")).hexdigest()
    return f"{_REDIS_CACHE_PREFIX}{digest}"


def _get_redis_client() -> redis.Redis | None:
    global _REDIS_CLIENT, _REDIS_UNAVAILABLE
    if _REDIS_UNAVAILABLE:
        return None
    if _REDIS_CLIENT is not None:
        return _REDIS_CLIENT

    settings = get_settings()
    if not settings.redis_url:
        _REDIS_UNAVAILABLE = True
        return None

    try:
        client = redis.from_url(
            settings.redis_url,
            socket_timeout=0.2,
            socket_connect_timeout=0.2,
            decode_responses=False,
        )
        # Ping único para no castigar cada request en caso de caída.
        client.ping()
        _REDIS_CLIENT = client
        return _REDIS_CLIENT
    except Exception:
        _REDIS_UNAVAILABLE = True
        return None


def _cache_get(query: str) -> list[float] | None:
    normalized = _normalized_query(query)
    key = _cache_key(query)
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            raw = redis_client.get(key)
            if raw:
                parsed = json.loads(raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw)
                if isinstance(parsed, list):
                    return [float(v) for v in parsed]
        except Exception:
            pass

    row = _EMBED_CACHE.get(normalized)
    if not row:
        return None
    ts, vector = row
    if (time.time() - ts) > _EMBED_CACHE_TTL_SEC:
        _EMBED_CACHE.pop(normalized, None)
        return None
    return vector


def _cache_set(query: str, vector: list[float]) -> None:
    normalized = _normalized_query(query)
    key = _cache_key(query)
    redis_client = _get_redis_client()
    if redis_client is not None:
        try:
            redis_client.setex(key, _EMBED_CACHE_TTL_SEC, json.dumps(vector))
            return
        except Exception:
            pass

    if len(_EMBED_CACHE) >= _EMBED_CACHE_MAX:
        oldest_key = min(_EMBED_CACHE, key=lambda k: _EMBED_CACHE[k][0])
        _EMBED_CACHE.pop(oldest_key, None)
    _EMBED_CACHE[normalized] = (time.time(), vector)


def _is_valid_http_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _score_to_label(score: float) -> tuple[str, str]:
    pct = int(round(score * 100))
    if score >= 0.90:
        return "Altamente relevante", f"{pct}% match con tu problema"
    if score >= 0.70:
        return "Muy relevante", f"{pct}% match con tu problema"
    return "Relevante", f"{pct}% match con tu problema"


def _normalize_case(raw: dict[str, Any]) -> dict[str, Any]:
    case_id = str(raw.get("case_id") or raw.get("id") or "")
    tipo = str(raw.get("tipo") or "AI").upper()
    score_raw = float(raw.get("score", 0.0))
    score_label, confidence = _score_to_label(score_raw)

    beneficios = raw.get("beneficios")
    if not isinstance(beneficios, list):
        beneficios = []

    stack = raw.get("stack") or raw.get("tecnologias")
    if not isinstance(stack, list):
        stack = []

    empresa = raw.get("empresa")
    industria = raw.get("industria") or raw.get("rubro")
    area = raw.get("area")
    has_valid_url = _is_valid_http_url(raw.get("url_slide"))
    has_kpi = bool(raw.get("kpi_impacto")) or bool(beneficios)

    quality = 0.0
    if has_valid_url:
        quality += 0.25
    if has_kpi:
        quality += 0.25
    if stack:
        quality += 0.2
    if empresa:
        quality += 0.15
    semantic_quality = raw.get("semantic_quality") or "basic"
    if semantic_quality == "good":
        quality += 0.15
    link_status = raw.get("link_status") or "unknown"

    similitud_semantica = max(0.0, min(1.0, score_raw))
    match_industria = 1.0 if industria and industria != "No mapeado" else 0.6
    match_area = 1.0 if area and area != "No mapeado" else 0.6
    confianza_fuente = float(raw.get("confianza_fuente", 1.0 if tipo == "NEO" else 0.85))
    recencia = 0.8
    final_score = (
        0.40 * similitud_semantica
        + 0.20 * match_industria
        + 0.15 * match_area
        + 0.15 * confianza_fuente
        + 0.10 * recencia
    )

    return {
        "case_id": case_id,
        "id": case_id,
        "tipo": tipo,
        "badge": "Ya ejecutado" if tipo == "NEO" else "Referencia externa",
        "titulo": raw.get("titulo") or "Caso sin titulo",
        "empresa": empresa or "No mapeado",
        "industria": industria or "No mapeado",
        "area": area or "No mapeado",
        "problema": raw.get("problema") or "No mapeado",
        "solucion": raw.get("solucion") or "No mapeado",
        "beneficios": beneficios,
        "stack": stack,
        "tecnologias": stack,
        "kpi_impacto": raw.get("kpi_impacto") or "No mapeado",
        "url_slide": raw.get("url_slide") if has_valid_url else None,
        "score": score_raw,
        "score_raw": score_raw,
        "score_label": score_label,
        "confidence": confidence,
        "score_final": round(final_score, 4),
        "score_breakdown": {
            "similitud_semantica": round(similitud_semantica, 4),
            "match_industria": round(match_industria, 4),
            "match_area": round(match_area, 4),
            "confianza_fuente": round(confianza_fuente, 4),
            "recencia": round(recencia, 4),
        },
        "confianza_fuente": confianza_fuente,
        "origen": raw.get("origen") or "unknown",
        "semantic_quality": semantic_quality,
        "link_status": link_status,
        "has_critical_evidence": has_valid_url and has_kpi,
        "data_quality_score": round(min(1.0, quality), 3),
    }


def _segment_cases(cases: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    neo_cases = [c for c in cases if c.get("tipo") == "NEO"]
    ai_cases = [c for c in cases if c.get("tipo") == "AI"]

    neo_cases.sort(key=lambda c: c.get("score_raw", 0.0), reverse=True)
    ai_cases.sort(key=lambda c: c.get("score_raw", 0.0), reverse=True)

    combined = neo_cases + ai_cases
    return neo_cases, ai_cases, combined


def _build_search_payload(
    problema: str,
    switch: SwitchType,
    raw_results: list[dict[str, Any]],
    latencia_ms: int,
    embedding_ms: int | None = None,
    qdrant_ms: int | None = None,
    cache_hit: bool | None = None,
) -> dict[str, Any]:
    normalized_all = [_normalize_case(c) for c in raw_results]
    with_evidence = [c for c in normalized_all if c.get("has_critical_evidence")]
    normalized = with_evidence if with_evidence else normalized_all
    global_top = max(normalized, key=lambda c: c.get("score_raw", 0.0), default=None)

    if switch == "both":
        neo_cases, ai_cases, casos = _segment_cases(normalized)
    elif switch == "neo":
        neo_cases = sorted(normalized, key=lambda c: c.get("score_raw", 0.0), reverse=True)
        ai_cases = []
        casos = neo_cases
    else:
        neo_cases = []
        ai_cases = sorted(normalized, key=lambda c: c.get("score_raw", 0.0), reverse=True)
        casos = ai_cases

    response: dict[str, Any] = {
        "status": "success",
        "problema_user": problema,
        "switch_usado": switch,
        "total": len(casos),
        "total_with_critical_evidence": len(with_evidence),
        "latencia_ms": latencia_ms,
        "nota": "NEO cases mostrados primero por confianza; score de relevancia siempre visible y desglosado.",
        "neo_cases": neo_cases,
        "ai_cases": ai_cases,
        "casos": casos,
    }
    if switch == "both" and global_top is not None:
        neo_top = max(neo_cases, key=lambda c: c.get("score_raw", 0.0), default=None)
        ai_top = max(ai_cases, key=lambda c: c.get("score_raw", 0.0), default=None)
        if ai_top and (not neo_top or (ai_top["score_raw"] - neo_top["score_raw"]) >= 0.08):
            response["top_match_global"] = ai_top
            response["top_match_global_reason"] = (
                "AI supera significativamente al mejor NEO en similitud; se muestra para transparencia."
            )

    if embedding_ms is not None:
        response["embedding_ms"] = embedding_ms
    if qdrant_ms is not None:
        response["qdrant_ms"] = qdrant_ms
    if cache_hit is not None:
        response["cache_hit"] = cache_hit

    return response


def search_cases_sync(
    problema: str,
    switch: SwitchType = "both",
    limit: int = 6,
    score_threshold: float = 0.50,
) -> dict[str, Any]:
    start = time.perf_counter()
    cached = _cache_get(problema)
    if cached is not None:
        query_vector = cached
    else:
        query_vector = db_connection.embed_query(problema)
        _cache_set(problema, query_vector)

    raw_results = db_connection.search_cases_by_vector(
        query_vector=query_vector,
        switch=switch,
        limit=limit,
        score_threshold=score_threshold,
        timeout_sec=1.0,
    )
    total_ms = int((time.perf_counter() - start) * 1000)
    return _build_search_payload(problema, switch, raw_results, total_ms)


async def search_cases_with_sla(
    problema: str,
    switch: SwitchType = "both",
    limit: int = 6,
    score_threshold: float = 0.50,
) -> dict[str, Any]:
    start = time.perf_counter()

    cached = _cache_get(problema)
    embed_start = time.perf_counter()
    cache_hit = cached is not None
    if cached is not None:
        query_vector = cached
    else:
        try:
            query_vector = await asyncio.wait_for(
                asyncio.to_thread(db_connection.embed_query, problema),
                timeout=2.0,
            )
            _cache_set(problema, query_vector)
        except asyncio.TimeoutError:
            fallback = _cache_get(problema)
            if fallback is None:
                raise ExternalDependencyTimeout("Gemini", 2.0)
            query_vector = fallback
    embedding_ms = int((time.perf_counter() - embed_start) * 1000)

    qdrant_start = time.perf_counter()
    try:
        raw_results = await asyncio.wait_for(
            asyncio.to_thread(
                db_connection.search_cases_by_vector,
                query_vector,
                switch,
                limit,
                score_threshold,
                1.0,
            ),
            timeout=1.0,
        )
    except asyncio.TimeoutError as exc:
        raise ExternalDependencyTimeout("Qdrant", 1.0) from exc
    qdrant_ms = int((time.perf_counter() - qdrant_start) * 1000)

    latencia_ms = int((time.perf_counter() - start) * 1000)
    return _build_search_payload(
        problema,
        switch,
        raw_results,
        latencia_ms=latencia_ms,
        embedding_ms=embedding_ms,
        qdrant_ms=qdrant_ms,
        cache_hit=cache_hit,
    )
