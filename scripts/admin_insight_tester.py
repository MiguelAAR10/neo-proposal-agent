"""Streamlit throwaway UI to test Sales Insight Collector end-to-end."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from typing import Any
import uuid

import requests
import streamlit as st

try:
    from sqlalchemy import create_engine, text

    HAS_SQLALCHEMY = True
except Exception:
    HAS_SQLALCHEMY = False


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

BACKEND_BASE_URL = os.getenv("INTEL_API_BASE_URL", "http://localhost:8000")
PROFILE_ENDPOINT_TEMPLATE = "/intel/company/{company_id}/profile"
INSIGHT_ENDPOINT_TEMPLATE = "/intel/company/{company_id}/insights"

COMPANY_OPTIONS = ["Banco_ABC", "Retail_XYZ", "Telco_123"]
AUTHOR_OPTIONS = ["Carlos Ruiz", "María Gómez", "Juan Pérez", "Ana Silva"]
FORM_AUTHOR_OPTIONS = ["Carlos Ruiz", "María Gómez", "Juan Pérez"]


def _sqlite_url() -> str:
    explicit_url = os.getenv("SQLITE_DB_URL") or os.getenv("INTEL_SQLITE_URL")
    if explicit_url:
        return explicit_url
    explicit_path = os.getenv("SQLITE_DB_PATH") or os.getenv("INTEL_SQLITE_PATH")
    if explicit_path:
        return f"sqlite:///{Path(explicit_path).expanduser().resolve()}"
    default_path = REPO_ROOT / "backend" / "data" / "intel.sqlite3"
    return f"sqlite:///{default_path.resolve()}"


def _engine():
    if not HAS_SQLALCHEMY:
        return None
    return create_engine(_sqlite_url(), future=True, connect_args={"check_same_thread": False})


def _ensure_tables() -> None:
    engine = _engine()
    if engine is None:
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_human_insights (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    author TEXT,
                    department TEXT,
                    sentiment TEXT,
                    raw_text TEXT NOT NULL,
                    structured_payload TEXT NOT NULL,
                    source TEXT NOT NULL,
                    parser_version TEXT NOT NULL,
                    insight_hash TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS intel_company_profiles (
                    id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    area TEXT NOT NULL,
                    profile_payload TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(company_id, area)
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_human_insights_company_created ON intel_human_insights (company_id, created_at)"
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_human_insights_department ON intel_human_insights (department)")
        )


def _stable_hash(company_id: str, author: str, raw_text: str) -> str:
    normalized = f"{company_id.strip().lower()}|{author.strip().lower()}|{raw_text.strip().lower()}"
    return sha256(normalized.encode("utf-8")).hexdigest()


def _structured_payload(text_value: str, sentiment: str) -> list[dict[str, Any]]:
    lowered = text_value.lower()
    decisor = "No identificado"
    for token in ("cfo", "cto", "ceo", "gerente", "director", "jefe"):
        if token in lowered:
            decisor = token
            break
    return [
        {"category": "pain_points", "value": text_value[:280], "confidence": 0.82},
        {"category": "decision_makers", "value": decisor, "confidence": 0.71},
        {"category": "sentiment", "value": sentiment, "confidence": 0.77},
    ]


def _seed_historical_dummy_data(company_id: str) -> dict[str, Any]:
    if not HAS_SQLALCHEMY:
        return {"status": "error", "detail": "SQLAlchemy no disponible en este entorno."}

    _ensure_tables()
    engine = _engine()
    now = datetime.now(timezone.utc)
    rows = [
        {
            "author": "Carlos Ruiz",
            "department": "Marketing",
            "sentiment": "Positivo",
            "raw_text": "Hace meses el área de Marketing priorizaba crecimiento y branding digital.",
            "source": "dummy_historical",
            "created_at": (now - timedelta(days=180)).isoformat(),  # ~6 meses
        },
        {
            "author": "María Gómez",
            "department": "Finanzas",
            "sentiment": "Riesgo",
            "raw_text": "Finanzas advirtió riesgo por presupuesto y exigió ROI claro antes de aprobar.",
            "source": "dummy_historical",
            "created_at": (now - timedelta(days=90)).isoformat(),  # ~3 meses
        },
        {
            "author": "Juan Pérez",
            "department": "TI",
            "sentiment": "Urgente",
            "raw_text": "TI reportó urgencia por deuda técnica y dependencia de sistemas legados.",
            "source": "dummy_historical",
            "created_at": (now - timedelta(days=7)).isoformat(),  # 1 semana
        },
        {
            "author": "Ana Silva",
            "department": "Comercial",
            "sentiment": "Bloqueo",
            "raw_text": "Comercial detectó bloqueo por proceso de compra y objeciones del comité.",
            "source": "dummy_historical",
            "created_at": (now - timedelta(days=1)).isoformat(),
        },
    ]

    inserted = 0
    updated = 0
    with engine.begin() as conn:
        for row in rows:
            payload = _structured_payload(row["raw_text"], row["sentiment"])
            insight_hash = _stable_hash(company_id, row["author"], row["raw_text"])
            existing = conn.execute(
                text("SELECT id FROM intel_human_insights WHERE insight_hash = :insight_hash LIMIT 1"),
                {"insight_hash": insight_hash},
            ).fetchone()

            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE intel_human_insights
                        SET company_id = :company_id,
                            author = :author,
                            department = :department,
                            sentiment = :sentiment,
                            raw_text = :raw_text,
                            structured_payload = :structured_payload,
                            source = :source,
                            parser_version = :parser_version,
                            created_at = :created_at
                        WHERE insight_hash = :insight_hash
                        """
                    ),
                    {
                        "company_id": company_id,
                        "author": row["author"],
                        "department": row["department"],
                        "sentiment": row["sentiment"],
                        "raw_text": row["raw_text"],
                        "structured_payload": json.dumps(payload, ensure_ascii=False),
                        "source": row["source"],
                        "parser_version": "v1-dummy",
                        "created_at": row["created_at"],
                        "insight_hash": insight_hash,
                    },
                )
                updated += 1
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO intel_human_insights (
                            id, company_id, author, department, sentiment,
                            raw_text, structured_payload, source, parser_version,
                            insight_hash, created_at
                        ) VALUES (
                            :id, :company_id, :author, :department, :sentiment,
                            :raw_text, :structured_payload, :source, :parser_version,
                            :insight_hash, :created_at
                        )
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "company_id": company_id,
                        "author": row["author"],
                        "department": row["department"],
                        "sentiment": row["sentiment"],
                        "raw_text": row["raw_text"],
                        "structured_payload": json.dumps(payload, ensure_ascii=False),
                        "source": row["source"],
                        "parser_version": "v1-dummy",
                        "insight_hash": insight_hash,
                        "created_at": row["created_at"],
                    },
                )
                inserted += 1

    return {
        "status": "ok",
        "company_id": company_id,
        "inserted": inserted,
        "updated": updated,
        "total_dummy_rows": len(rows),
    }


def _post_current_insight(company_id: str, author: str, raw_text: str) -> dict[str, Any]:
    url = f"{BACKEND_BASE_URL.rstrip('/')}{INSIGHT_ENDPOINT_TEMPLATE.format(company_id=company_id)}"
    payload = {
        "author": author,
        "text": raw_text,
        "source": "streamlit_admin_test",
    }
    try:
        response = requests.post(url, json=payload, timeout=25)
        body = response.json() if response.content else {}
        return {
            "http_status": response.status_code,
            "url": url,
            "payload": payload,
            "response": body,
        }
    except Exception as exc:
        return {
            "http_status": None,
            "url": url,
            "payload": payload,
            "response": {"error": str(exc)},
        }


def _refresh_profile_snapshot(company_id: str) -> dict[str, Any]:
    """
    Ejecuta localmente update_summary_node para forzar consolidación de perfil
    con la lógica de time-decay antes de leer el perfil guardado.
    """
    try:
        from src.agent.nodes import update_summary_node

        state = {
            "empresa": company_id,
            "area": "General",
            "perfil_cliente": {"empresa": company_id, "area": "General"},
            "inteligencia_sector": {
                "industria": "General",
                "area": "General",
                "source": "streamlit_dummy_context",
                "tendencias": [],
                "benchmarks": {},
                "oportunidades": [],
            },
            "error": "",
        }
        result = update_summary_node(state)
        return {
            "status": "ok",
            "human_insights": result.get("human_insights", []),
            "perfil_cliente": result.get("perfil_cliente", {}),
        }
    except Exception as exc:
        return {
            "status": "error",
            "detail": str(exc),
        }


def _load_profile_from_db(company_id: str) -> dict[str, Any]:
    if not HAS_SQLALCHEMY:
        return {"status": "error", "detail": "SQLAlchemy no disponible para leer perfil."}

    _ensure_tables()
    engine = _engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT profile_payload, updated_at
                FROM intel_company_profiles
                WHERE company_id = :company_id
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ),
            {"company_id": company_id},
        ).fetchone()

    if not row:
        return {"status": "empty", "detail": "No hay perfil consolidado para esta empresa."}

    payload_raw = row[0]
    if isinstance(payload_raw, str):
        try:
            payload = json.loads(payload_raw)
        except Exception:
            payload = {"raw": payload_raw}
    else:
        payload = payload_raw

    return {
        "status": "ok",
        "updated_at": row[1],
        "profile_payload": payload,
    }


def _try_get_profile_endpoint(company_id: str) -> dict[str, Any]:
    url = f"{BACKEND_BASE_URL.rstrip('/')}{PROFILE_ENDPOINT_TEMPLATE.format(company_id=company_id)}"
    try:
        response = requests.get(url, timeout=15)
        body = response.json() if response.content else {}
        return {
            "http_status": response.status_code,
            "url": url,
            "body": body,
        }
    except Exception as exc:
        return {
            "http_status": None,
            "url": url,
            "body": {"error": str(exc)},
        }


def _render_profile_markdown(profile_payload: dict[str, Any]) -> str:
    summary = profile_payload.get("resumen_departamentos") if isinstance(profile_payload, dict) else None
    lines = ["### Evolution Summary (Time-Decay)"]
    if isinstance(summary, dict):
        departments = summary.get("departments") or []
        if departments:
            for dep in departments:
                lines.append(f"- **{dep.get('department', 'General')}**: {dep.get('current_state', 'N/A')}")
                signals = dep.get("priority_signals_recent") or []
                if signals:
                    lines.append(f"  - Señales recientes: {signals}")
                hist = dep.get("historical_notes")
                if hist:
                    lines.append(f"  - Evolución histórica: {hist}")
        historical = summary.get("historical_evolution")
        if historical:
            lines.append(f"\n**Evolución Global:** {historical}")
        lines.append(f"\n_Fuente resumen: {summary.get('source', 'N/A')}_")
    else:
        lines.append("No hay `resumen_departamentos` aún. Inyecta dummy data y procesa un insight actual.")

    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Motor de Inteligencia Comercial", layout="wide")
    st.title("🕵️‍♂️ Motor de Inteligencia Comercial (Test de Ventas)")

    if not HAS_SQLALCHEMY:
        st.warning("SQLAlchemy no está disponible en este entorno. Instala dependencias antes de usar el seeder.")

    if "last_endpoint_response" not in st.session_state:
        st.session_state["last_endpoint_response"] = None
    if "last_profile_snapshot" not in st.session_state:
        st.session_state["last_profile_snapshot"] = None
    if "last_get_attempt" not in st.session_state:
        st.session_state["last_get_attempt"] = None
    if "last_seed_report" not in st.session_state:
        st.session_state["last_seed_report"] = None

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Controles e Inputs")
        selected_company = st.selectbox("Selector de Empresa", options=COMPANY_OPTIONS)
        normalized_company = selected_company.strip()

        if st.button("Inyectar Dummy Data Histórica", use_container_width=True):
            seed_report = _seed_historical_dummy_data(normalized_company)
            st.session_state["last_seed_report"] = seed_report
            refresh = _refresh_profile_snapshot(normalized_company)
            st.session_state["last_profile_snapshot"] = refresh
            st.session_state["last_get_attempt"] = _try_get_profile_endpoint(normalized_company)

        if st.session_state["last_seed_report"] is not None:
            st.json(st.session_state["last_seed_report"])

        st.markdown("---")
        st.markdown("#### Formulario de Nuevo Insight")
        author = st.selectbox("Consultor", options=FORM_AUTHOR_OPTIONS)
        raw_report = st.text_area(
            "Reporte crudo de reunión",
            height=220,
            placeholder=(
                "Ejemplo: El área de Finanzas mantiene riesgo por presupuesto, "
                "pero TI reporta urgencia por modernización en 30 días."
            ),
        )

        if st.button("Procesar Insight Actual", type="primary", use_container_width=True):
            st.session_state["last_endpoint_response"] = _post_current_insight(
                company_id=normalized_company,
                author=author,
                raw_text=raw_report,
            )
            st.session_state["last_profile_snapshot"] = _refresh_profile_snapshot(normalized_company)
            st.session_state["last_get_attempt"] = _try_get_profile_endpoint(normalized_company)

    with right_col:
        st.subheader("Resultados y Observabilidad")
        st.markdown("#### Respuesta cruda del endpoint")
        if st.session_state["last_endpoint_response"] is None:
            st.info("Aún no se ha procesado un insight actual.")
        else:
            st.json(st.session_state["last_endpoint_response"])

        st.markdown("---")
        st.markdown("#### GET de perfil actualizado")
        if st.session_state["last_get_attempt"] is not None:
            st.json(st.session_state["last_get_attempt"])

        st.markdown("---")
        st.markdown("#### Evolution Summary final")
        profile_snapshot = st.session_state.get("last_profile_snapshot") or {}
        if profile_snapshot.get("status") == "ok":
            profile_payload = profile_snapshot.get("perfil_cliente") or {}
            st.markdown(_render_profile_markdown(profile_payload))
            st.json(profile_payload)
        else:
            db_profile = _load_profile_from_db(selected_company.strip())
            if db_profile.get("status") == "ok":
                st.markdown(_render_profile_markdown(db_profile.get("profile_payload") or {}))
                st.json(db_profile)
            else:
                st.info("No hay perfil consolidado disponible aún para esta empresa.")
                st.json(db_profile)


if __name__ == "__main__":
    main()
