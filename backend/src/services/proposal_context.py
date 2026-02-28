from __future__ import annotations

from typing import Any


def filter_selected_cases(all_cases: list[dict[str, Any]], selected_ids: list[str]) -> list[dict[str, Any]]:
    selected = {str(case_id) for case_id in selected_ids}
    return [case for case in all_cases if str(case.get("id")) in selected]


def validate_selected_cases_have_url(selected_cases: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    missing_url_ids: list[str] = []
    for case in selected_cases:
        if not case.get("url_slide"):
            missing_url_ids.append(str(case.get("id")))
    return (len(missing_url_ids) == 0, missing_url_ids)


def format_cases_for_prompt(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return "No hay casos seleccionados."

    blocks: list[str] = []
    for idx, case in enumerate(cases, start=1):
        beneficios = case.get("beneficios", [])
        if isinstance(beneficios, list):
            beneficios_txt = ", ".join(str(v) for v in beneficios if str(v).strip()) or "N/A"
        else:
            beneficios_txt = str(beneficios or "N/A")

        blocks.append(
            f"--- CASO {idx} ---\n"
            f"ID: {case.get('id', 'N/A')}\n"
            f"TIPO: {case.get('tipo', 'N/A')}\n"
            f"TITULO: {case.get('titulo', 'Sin titulo')}\n"
            f"PROBLEMA: {case.get('resumen', case.get('problema', 'N/A'))}\n"
            f"SOLUCION: {case.get('solucion', 'Ver slide original')}\n"
            f"BENEFICIOS: {beneficios_txt}\n"
            f"KPI: {case.get('kpi_impacto', 'N/A')}\n"
            f"EVIDENCIA: {case.get('evidence_label', 'N/A')}\n"
            f"URL: {case.get('url_slide', 'N/A')}"
        )
    return "\n\n".join(blocks)
