from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from src.config import get_settings
from src.models.industry_radar import RadarSignal
from src.services.errors import RadarToolTimeoutError, RadarToolUnavailableError


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(
    *,
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    timeout_sec: float = 8.0,
) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    req = Request(url=url, data=payload, method=method, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout_sec) as response:
            text = response.read().decode("utf-8")
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
    except TimeoutError as exc:
        raise RadarToolTimeoutError(f"Timeout llamando tool externo: {url}") from exc
    except URLError as exc:
        raise RadarToolUnavailableError(f"Tool externo no disponible: {url}") from exc
    except Exception as exc:
        raise RadarToolUnavailableError(f"Fallo integracion tool externo: {url} ({exc})") from exc


def _is_live_enabled(force_mock_tools: bool = False) -> bool:
    settings = get_settings()
    return bool(settings.radar_use_live_tools and not force_mock_tools)


def _build_mock_trend_signals(industry_target: str) -> list[RadarSignal]:
    low = industry_target.strip().lower()
    if "banca" in low or "finanz" in low:
        texts = [
            "Reporte consultora: presión de reducción de costos en canales digitales bancarios.",
            "Tendencia mercado: mayor demanda de modelos antifraude con IA explicable.",
        ]
    else:
        texts = [
            f"Tendencia mercado en {industry_target}: foco en eficiencia operativa y automatización.",
            f"Reporte de industria {industry_target}: prioridad en time-to-value y quick wins.",
        ]
    return [
        RadarSignal(
            source="market_trends_mock",
            signal_type="market_trend",
            content=text,
            confidence=0.62,
            captured_at=_now_iso(),
        )
        for text in texts
    ]


def search_market_trends(industry_target: str, *, force_mock_tools: bool = False) -> list[RadarSignal]:
    settings = get_settings()
    if not _is_live_enabled(force_mock_tools):
        return _build_mock_trend_signals(industry_target)

    query = f"latest market trends {industry_target} LATAM enterprise technology"
    if settings.tavily_api_key:
        data = _http_json(
            url="https://api.tavily.com/search",
            method="POST",
            headers={"Content-Type": "application/json"},
            body={
                "api_key": settings.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 4,
            },
            timeout_sec=settings.radar_tool_timeout_sec,
        )
        results = data.get("results") if isinstance(data.get("results"), list) else []
        signals = []
        for row in results[:4]:
            content = str(row.get("content") or row.get("snippet") or "").strip()
            if not content:
                continue
            signals.append(
                RadarSignal(
                    source="tavily",
                    signal_type="market_trend",
                    content=content[:1800],
                    confidence=0.75,
                    captured_at=_now_iso(),
                )
            )
        return signals or _build_mock_trend_signals(industry_target)

    if settings.perplexity_api_key:
        data = _http_json(
            url="https://api.perplexity.ai/chat/completions",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.perplexity_api_key}",
            },
            body={
                "model": "sonar",
                "messages": [{"role": "user", "content": f"Summarize latest market trends for {industry_target}."}],
                "temperature": 0.1,
            },
            timeout_sec=settings.radar_tool_timeout_sec,
        )
        choices = data.get("choices") if isinstance(data.get("choices"), list) else []
        if choices:
            content = str((((choices[0] or {}).get("message") or {}).get("content")) or "").strip()
            if content:
                return [
                    RadarSignal(
                        source="perplexity",
                        signal_type="market_trend",
                        content=content[:1800],
                        confidence=0.72,
                        captured_at=_now_iso(),
                    )
                ]

    return _build_mock_trend_signals(industry_target)


def scrape_regulatory_site(industry_target: str, *, force_mock_tools: bool = False) -> list[RadarSignal]:
    settings = get_settings()
    low = industry_target.strip().lower()
    target_url = "https://www.sbs.gob.pe" if ("banca" in low or "finanz" in low) else "https://www.elperuano.pe"

    if not _is_live_enabled(force_mock_tools) or not settings.firecrawl_api_key:
        markdown = (
            f"# Boletín regulatorio ({industry_target})\n"
            "- Resolución reciente exige mayor trazabilidad de procesos críticos.\n"
            "- Nueva circular sugiere controles reforzados para gestión de riesgo operativo.\n"
        )
        return [
            RadarSignal(
                source="regulatory_mock",
                signal_type="regulatory",
                content=markdown,
                confidence=0.68,
                captured_at=_now_iso(),
            )
        ]

    data = _http_json(
        url="https://api.firecrawl.dev/v1/scrape",
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.firecrawl_api_key}",
        },
        body={
            "url": target_url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
        timeout_sec=settings.radar_tool_timeout_sec,
    )
    content = str((data.get("data") or {}).get("markdown") or "").strip()
    if not content:
        raise RadarToolUnavailableError("Firecrawl no devolvio markdown util")

    return [
        RadarSignal(
            source="firecrawl",
            signal_type="regulatory",
            content=content[:2000],
            confidence=0.76,
            captured_at=_now_iso(),
        )
    ]


def get_financial_ticker(ticker: str, *, force_mock_tools: bool = False) -> list[RadarSignal]:
    settings = get_settings()
    normalized_ticker = (ticker or "").strip().upper() or "BAP"

    if _is_live_enabled(force_mock_tools):
        try:
            import yfinance as yf  # type: ignore

            hist = yf.Ticker(normalized_ticker).history(period="5d")
            if len(hist) >= 2:
                close_prev = float(hist["Close"].iloc[-2])
                close_curr = float(hist["Close"].iloc[-1])
                if close_prev > 0:
                    pct = ((close_curr - close_prev) / close_prev) * 100.0
                    text = f"Ticker {normalized_ticker} variación diaria: {pct:.2f}%."
                    return [
                        RadarSignal(
                            source="yfinance",
                            signal_type="financial_ticker",
                            content=text,
                            confidence=0.78,
                            captured_at=_now_iso(),
                        )
                    ]
        except Exception:
            pass

    digest = hashlib.sha256(normalized_ticker.encode("utf-8")).hexdigest()
    base = int(digest[:8], 16) % 1500  # 0..1499
    pct = (base / 100.0) - 7.5  # -7.5..+7.49
    text = f"Ticker {normalized_ticker} variación diaria estimada (mock): {pct:.2f}%."
    return [
        RadarSignal(
            source="financial_mock",
            signal_type="financial_ticker",
            content=text,
            confidence=0.55,
            captured_at=_now_iso(),
        )
    ]
