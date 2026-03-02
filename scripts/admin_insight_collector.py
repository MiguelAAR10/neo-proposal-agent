"""Gradio admin tool for testing Sales Insight Collector endpoint."""

from __future__ import annotations

import json
import os
from typing import Any

import gradio as gr
import requests

BACKEND_BASE_URL = os.getenv("INTEL_API_BASE_URL", "http://localhost:8000")
ENDPOINT_TEMPLATE = "/intel/company/{company_id}/insights"
DEFAULT_SOURCE = "admin_gradio"

COMPANY_OPTIONS = [
    "banco-abc",
    "retail-xyz",
    "telco-123",
]

AUTHOR_OPTIONS = [
    "Carlos Ruiz",
    "María Gómez",
    "Juan Pérez",
    "Ana Silva",
]


def _pretty(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def process_insight(company_id: str, author: str, raw_report: str) -> str:
    report = (raw_report or "").strip()
    if not company_id:
        return _pretty({"error": "company_id es obligatorio"})
    if not author:
        return _pretty({"error": "author es obligatorio"})
    if not report:
        return _pretty({"error": "El reporte no puede estar vacío"})

    url = f"{BACKEND_BASE_URL.rstrip('/')}{ENDPOINT_TEMPLATE.format(company_id=company_id)}"
    payload = {
        "author": author,
        "text": report,
        "source": DEFAULT_SOURCE,
    }

    try:
        response = requests.post(url, json=payload, timeout=25)
    except requests.RequestException as exc:
        return _pretty(
            {
                "status": "network_error",
                "url": url,
                "detail": str(exc),
            }
        )

    try:
        body = response.json()
    except ValueError:
        body = {"raw_response": response.text}

    return _pretty(
        {
            "http_status": response.status_code,
            "response": body,
        }
    )


def build_app() -> gr.Blocks:
    with gr.Blocks(title="NEO - Sales Insight Collector (Admin Test)") as app:
        gr.Markdown("# NEO - Sales Insight Collector (Admin Test)")

        company_id = gr.Dropdown(
            label="Company ID",
            choices=COMPANY_OPTIONS,
            value=COMPANY_OPTIONS[0],
            interactive=True,
        )
        author = gr.Dropdown(
            label="Consultor (author)",
            choices=AUTHOR_OPTIONS,
            value=AUTHOR_OPTIONS[0],
            interactive=True,
        )
        raw_report = gr.Textbox(
            label="Reporte de reunión (texto libre)",
            lines=12,
            placeholder=(
                "Ejemplo: Cliente teme sobrecostos, CFO pide ROI en 90 días, "
                "competidor principal ofrece piloto sin costo..."
            ),
        )
        submit = gr.Button("Procesar y Guardar Insight", variant="primary")
        output = gr.Code(label="Respuesta Backend", language="json", interactive=False)

        submit.click(fn=process_insight, inputs=[company_id, author, raw_report], outputs=output)

    return app


if __name__ == "__main__":
    ui = build_app()
    ui.launch(server_name="0.0.0.0", server_port=7861)
