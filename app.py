from uuid import uuid4

import streamlit as st

from src.agent.graph import graph


st.set_page_config(page_title="NEO Proposal Agent", page_icon="🧩", layout="wide")
st.title("NEO Proposal Agent")
st.caption("Generador de propuestas comerciales con LangGraph + Streamlit")


def _new_thread_config() -> dict:
    return {"configurable": {"thread_id": f"demo_{uuid4().hex[:8]}"}}


if "graph_config" not in st.session_state:
    st.session_state.graph_config = _new_thread_config()
if "busy" not in st.session_state:
    st.session_state.busy = False

config = st.session_state.graph_config
thread_id = config["configurable"]["thread_id"]

with st.sidebar:
    st.markdown("### Sesion")
    st.code(thread_id)
    if st.button("Nueva Sesion", disabled=st.session_state.busy):
        st.session_state.graph_config = _new_thread_config()
        st.session_state.busy = False
        st.rerun()

try:
    snapshot = graph.get_state(config)
except Exception:
    snapshot = None

values = dict(snapshot.values) if snapshot and snapshot.values else {}
next_nodes = list(snapshot.next) if snapshot and snapshot.next else []

error_msg = values.get("error", "") if values else ""
propuesta_final = values.get("propuesta_final", "") if values else ""
casos_encontrados = values.get("casos_encontrados", []) if values else []
is_paused_for_draft = "draft_node" in next_nodes

st.subheader("1) Formulario Inicial")
def_empresa = values.get("empresa", "") if values else ""
def_rubro = values.get("rubro", "") if values else ""
def_problema = values.get("problema", "") if values else ""

with st.form("initial_form"):
    empresa = st.text_input("Empresa", value=def_empresa)
    rubro = st.text_input("Rubro", value=def_rubro)
    problema = st.text_area("Problema", value=def_problema, height=140)
    submit_search = st.form_submit_button("Buscar Casos", disabled=st.session_state.busy)

if submit_search and not st.session_state.busy:
    st.session_state.busy = True
    try:
        # Cada busqueda arranca en un thread nuevo para evitar estados viejos atascados.
        st.session_state.graph_config = _new_thread_config()
        config = st.session_state.graph_config

        initial_state = {
            "empresa": empresa,
            "rubro": rubro,
            "problema": problema,
            "casos_encontrados": [],
            "casos_seleccionados_ids": [],
            "propuesta_final": "",
            "error": "",
        }
        graph.invoke(initial_state, config=config)
    except Exception as exc:
        st.error(f"Error iniciando flujo: {exc}")
    finally:
        st.session_state.busy = False
    st.rerun()

st.subheader("2) Seleccion de Casos (HITL)")
if is_paused_for_draft and not propuesta_final:
    if casos_encontrados:
        with st.form("select_cases_form"):
            st.write("Selecciona los casos a usar en la propuesta:")
            selected_ids: list[str] = []
            for case in casos_encontrados:
                case_id = str(case.get("id", ""))
                label = f"{case.get('titulo', 'Sin titulo')} (ID: {case_id})"
                checked = st.checkbox(label, key=f"case_{case_id}")
                resumen = str(case.get("resumen", "")).strip()
                if resumen:
                    st.caption(resumen)
                if checked:
                    selected_ids.append(case_id)

            submit_draft = st.form_submit_button("Generar Propuesta", disabled=st.session_state.busy)

        if submit_draft and not st.session_state.busy:
            st.session_state.busy = True
            try:
                if not selected_ids:
                    st.error("Selecciona al menos un caso.")
                else:
                    graph.update_state(config, {"casos_seleccionados_ids": selected_ids, "error": ""})
                    graph.invoke(None, config=config)
                    st.rerun()
            except Exception as exc:
                st.error(f"Error al reanudar el flujo: {exc}")
            finally:
                st.session_state.busy = False
    else:
        st.warning("No hay casos para seleccionar.")
elif values and not propuesta_final and not error_msg:
    st.info("Esperando resultados del paso de recuperacion.")

st.subheader("3) Resultado")
if error_msg:
    st.error(error_msg)

if propuesta_final:
    st.markdown("### Propuesta Generada")
    st.markdown(propuesta_final)
