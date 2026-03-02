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
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    HAS_SQLALCHEMY = True
except Exception:
    HAS_SQLALCHEMY = False


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

try:
    from src.repositories.sqlite_repositories import Base, HumanInsightORM

    HAS_BACKEND_ORM = True
except Exception:
    Base = None  # type: ignore[assignment]
    HumanInsightORM = None  # type: ignore[assignment]
    HAS_BACKEND_ORM = False

BACKEND_BASE_URL = os.getenv("INTEL_API_BASE_URL", "http://localhost:8000")
INSIGHT_ENDPOINT_TEMPLATE = "/intel/company/{company_id}/insights"
PROFILE_ENDPOINT_TEMPLATE = "/intel/company/{company_id}/profile"

COMPANY_OPTIONS = ["Banco_ABC", "Retail_XYZ", "Telco_123"]
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


def _reset_and_seed_historical_dummy_data(company_id: str) -> dict[str, Any]:
    if not HAS_SQLALCHEMY:
        return {"status": "error", "detail": "SQLAlchemy no disponible en este entorno."}
    if not HAS_BACKEND_ORM:
        return {
            "status": "error",
            "detail": "No se pudieron cargar Base/HumanInsightORM del backend para reset de esquema.",
        }

    engine = _engine()
    assert engine is not None

    # Hard reset solicitado por arquitectura para evitar desalineación de columnas.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    now = datetime.now(timezone.utc)
    rows = [
        {
            "author": "Carlos Ruiz",
            "department": "Marketing",
            "sentiment": "Positivo",
            "insight": "Lanzaron una campaña exitosa, pero no tienen más presupuesto este año",
            "created_at": now - timedelta(days=180),  # Hace 6 meses
        },
        {
            "author": "María Gómez",
            "department": "Finanzas",
            "sentiment": "Riesgo",
            "insight": "El CFO está preocupado por los costos de licencias en la nube",
            "created_at": now - timedelta(days=90),  # Hace 3 meses
        },
        {
            "author": "Juan Pérez",
            "department": "TI",
            "sentiment": "Bloqueo",
            "insight": "TI frenó todas las compras de software porque están migrando sus servidores",
            "created_at": now - timedelta(days=14),  # Hace 2 semanas
        },
        {
            "author": "Ana Silva",
            "department": "Innovación",
            "sentiment": "Urgente",
            "insight": "El CEO quiere implementar Inteligencia Artificial urgente para no quedarse atrás de la competencia",
            "created_at": now - timedelta(days=1),  # Hace 1 día
        },
    ]

    inserted = 0
    with SessionLocal() as session:
        for row in rows:
            raw_text = row["insight"]
            record = HumanInsightORM(
                id=str(uuid.uuid4()),
                company_id=company_id,
                author=row["author"],
                department=row["department"],
                sentiment=row["sentiment"],
                raw_text=raw_text,
                structured_payload=_structured_payload(raw_text, row["sentiment"]),
                source="dummy_historical_streamlit",
                parser_version="v1-dummy",
                insight_hash=_stable_hash(company_id, row["author"], raw_text),
                created_at=row["created_at"],
            )
            session.add(record)
            inserted += 1
        session.commit()

    return {
        "status": "ok",
        "action": "hard_reset_and_seed",
        "company_id": company_id,
        "inserted": inserted,
        "records": [
            {
                "author": r["author"],
                "department": r["department"],
                "sentiment": r["sentiment"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in rows
        ],
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
    """Ejecuta update_summary local para consolidar perfil con lógica time-decay."""
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

    engine = _engine()
    if engine is None:
        return {"status": "error", "detail": "No se pudo crear engine SQLite."}

    with engine.begin() as conn:
        row = conn.exec_driver_sql(
            """
            SELECT profile_payload, updated_at
            FROM intel_company_profiles
            WHERE company_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (company_id,),
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
        lines.append("No hay `resumen_departamentos` aún. Resetea/inyecta data y procesa un insight actual.")

    return "\n".join(lines)


def main() -> None:
    st.set_page_config(page_title="Motor de Inteligencia Comercial", layout="wide")
    st.title("🕵️‍♂️ Motor de Inteligencia Comercial (Test de Ventas)")

    st.markdown(
        """
        <style>
            div.stButton > button[kind="primary"] {
                background-color: #c62828;
                border-color: #c62828;
                color: white;
            }
            div.stButton > button[kind="primary"]:hover {
                background-color: #b71c1c;
                border-color: #b71c1c;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

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

        if st.button("Resetear Base de Datos e Inyectar Dummy Data", type="primary", use_container_width=True):
            seed_report = _reset_and_seed_historical_dummy_data(normalized_company)
            st.session_state["last_seed_report"] = seed_report
            st.session_state["last_profile_snapshot"] = _refresh_profile_snapshot(normalized_company)
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
                "Ejemplo: TI sigue en bloqueo de compras, pero el CEO presiona por IA inmediata."
            ),
        )

        if st.button("Procesar Insight Actual", use_container_width=True):
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
            db_profile = _load_profile_from_db(normalized_company)
            if db_profile.get("status") == "ok":
                st.markdown(_render_profile_markdown(db_profile.get("profile_payload") or {}))
                st.json(db_profile)
            else:
                st.info("No hay perfil consolidado disponible aún para esta empresa.")
                st.json(db_profile)


if __name__ == "__main__":
    main()
