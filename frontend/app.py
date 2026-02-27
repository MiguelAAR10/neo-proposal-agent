"""
app.py — NEO Intelligence Platform
UI: Búsqueda semántica de casos + Chat RAG integrado
Run: streamlit run app.py
"""
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# --- CÓDIGO A PRUEBA DE BALAS PARA LA CONEXIÓN ---
if "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"] # Lee de la nube
else:
    API_URL = os.getenv("API_URL", "http://localhost:8000") # Lee en local

# Asegúrate de limpiar la URL por si acaso
API_URL = API_URL.rstrip("/")

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="NEO Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Dark premium design
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a1628 100%);
    color: #e6edf3;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 2rem; max-width: 1200px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid #21262d;
}
[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem; }

/* ── Logo / Header ── */
.neo-logo {
    font-size: 1.6rem;
    font-weight: 700;
    background: linear-gradient(90deg, #58a6ff, #7ee8fa, #80ff72);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
    margin-bottom: 0.2rem;
}
.neo-tagline {
    font-size: 0.78rem;
    color: #6e7681;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* ── Section headers ── */
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
    margin-top: 1.4rem;
}

/* ── Input: text area ── */
.stTextArea textarea {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.9rem !important;
    transition: border-color 0.2s;
}
.stTextArea textarea:focus {
    border-color: #388bfd !important;
    box-shadow: 0 0 0 3px rgba(56,139,253,0.15) !important;
}

/* ── Select / Slider ── */
.stSelectbox > div > div {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
}
.stSlider > div > div > div { background: #388bfd !important; }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #388bfd, #0d5bce) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.5rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(56,139,253,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(56,139,253,0.4) !important;
}
.stButton > button[kind="secondary"] {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #30363d !important;
    border-color: #388bfd !important;
}

/* ── Case card ── */
.case-card {
    background: linear-gradient(145deg, #161b22, #0d1117);
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
    transition: all 0.25s ease;
    position: relative;
    overflow: hidden;
}
.case-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 100%;
    border-radius: 14px 0 0 14px;
}
.case-card.score-high::before  { background: linear-gradient(180deg, #3fb950, #2ea043); }
.case-card.score-mid::before   { background: linear-gradient(180deg, #f0b429, #d99e00); }
.case-card.score-low::before   { background: linear-gradient(180deg, #f78166, #da3633); }
.case-card:hover {
    border-color: #388bfd;
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}

.case-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem; }
.case-empresa { font-size: 1.05rem; font-weight: 700; color: #e6edf3; }
.case-id { font-size: 0.72rem; color: #6e7681; font-family: monospace; }

.score-badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 12px; border-radius: 20px;
    font-size: 0.8rem; font-weight: 700;
}
.score-high { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.score-mid  { background: rgba(240,180,41,0.15); color: #f0b429; border: 1px solid rgba(240,180,41,0.3); }
.score-low  { background: rgba(247,129,102,0.15); color: #f78166; border: 1px solid rgba(247,129,102,0.3); }

.tag-pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    margin: 2px;
    background: #21262d;
    color: #8b949e;
    border: 1px solid #30363d;
}
.tag-industry { background: rgba(56,139,253,0.1); color: #58a6ff; border-color: rgba(56,139,253,0.25); }
.tag-area     { background: rgba(126,232,250,0.1); color: #7ee8fa; border-color: rgba(126,232,250,0.25); }
.tag-trigger  { background: rgba(128,255,114,0.1); color: #80ff72; border-color: rgba(128,255,114,0.25); }

.relevance-box {
    background: rgba(56,139,253,0.08);
    border: 1px solid rgba(56,139,253,0.2);
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    color: #79c0ff;
}

.field-label {
    font-size: 0.72rem;
    font-weight: 600;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
    margin-top: 0.9rem;
}
.field-value {
    font-size: 0.92rem;
    color: #c9d1d9;
    line-height: 1.6;
}

.results-box {
    background: rgba(63,185,80,0.08);
    border: 1px solid rgba(63,185,80,0.2);
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    font-size: 0.88rem;
    color: #3fb950;
    margin-top: 0.5rem;
}

/* ── Chat ── */
.chat-container {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 14px;
    padding: 1.2rem;
    min-height: 320px;
    max-height: 480px;
    overflow-y: auto;
    margin-bottom: 1rem;
}
.chat-bubble-user {
    background: linear-gradient(135deg, #1f3a5f, #0d2444);
    border: 1px solid rgba(56,139,253,0.2);
    border-radius: 12px 12px 2px 12px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0 0.5rem 15%;
    color: #e6edf3;
    font-size: 0.92rem;
}
.chat-bubble-assistant {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px 12px 12px 2px;
    padding: 0.7rem 1rem;
    margin: 0.5rem 15% 0.5rem 0;
    color: #c9d1d9;
    font-size: 0.92rem;
    line-height: 1.6;
}
.chat-name {
    font-size: 0.7rem;
    font-weight: 600;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.chat-name-user { color: #58a6ff; }
.chat-name-bot  { color: #80ff72; }

/* ── Divider ── */
.neo-divider {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.5rem 0;
}

/* ── Stat pills in sidebar ── */
.stat-pill {
    display: flex; justify-content: space-between; align-items: center;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 0.5rem 0.8rem;
    margin-bottom: 0.4rem;
    font-size: 0.82rem;
}
.stat-label { color: #8b949e; }
.stat-value { color: #e6edf3; font-weight: 600; }

/* ── Expander ── */
details { border: none !important; }
summary { 
    background: transparent !important;
    color: #8b949e !important;
    font-size: 0.82rem !important;
    padding: 0.3rem 0 !important;
}

/* ── No results ── */
.empty-state {
    text-align: center;
    padding: 3rem;
    color: #6e7681;
}
.empty-state .icon { font-size: 3rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA
# ─────────────────────────────────────────────
INDUSTRIAS = [
    "", "Servicios Financieros", "Consumo y Retail", "Tecnología y Telecom",
    "Salud y Farmacéutica", "Industria y Energía", "Agro y Logística",
    "Educación", "Gobierno y Sector Público", "Inmobiliario",
]
AREAS = [
    "", "Operaciones", "Ventas", "Marketing", "Growth", "Comercial",
    "Producto", "Logística", "Estrategia", "Transformación Digital", "Customer Experience",
]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def call_search(query: str, industria: str, area: str, top_k: int) -> list[dict]:
    payload = {
        "query": query,
        "industria": industria if industria else None,
        "area_funcional": area if area else None,
        "top_k": top_k,
    }
    resp = requests.post(f"{API_URL}/search", json=payload, timeout=40)
    resp.raise_for_status()
    return resp.json()


def call_chat(message: str, cases_context: list[dict], history: list[dict], session_id: str) -> str:
    payload = {
        "message": message,
        "cases_context": cases_context,
        "history": history,
        "session_id": session_id,
    }
    resp = requests.post(f"{API_URL}/chat", json=payload, timeout=75)
    resp.raise_for_status()
    data = resp.json()
    return data.get("reply", "No se recibió respuesta del asistente.")


def score_class(score: float) -> str:
    if score >= 0.80: return "high"
    if score >= 0.65: return "mid"
    return "low"


def score_icon(score: float) -> str:
    if score >= 0.80: return "🟢"
    if score >= 0.65: return "🟡"
    return "🟠"


def render_case_card(i: int, case: dict, expanded: bool = True):
    sc = score_class(case["score"])
    score_pct = int(case["score"] * 100)
    icon = score_icon(case["score"])

    tags_html = f"""<span class="tag-pill tag-industry">{case.get('industria', 'N/A')}</span>
<span class="tag-pill tag-area">{case.get('area_funcional', 'N/A')}</span>"""
    if case.get("trigger_comercial"):
        tags_html += f'<span class="tag-pill tag-trigger">🎯 {case["trigger_comercial"]}</span>'

    header_html = f"""<div class="case-card score-{sc}" id="case-{i}">
<div class="case-header">
    <div>
        <div class="case-empresa">{icon} {case.get('empresa', 'N/A')}</div>
        <div class="case-id">#{case.get('id_caso', 'N/A')}</div>
    </div>
    <div class="score-badge score-{sc}">
        {'▲' if sc == 'high' else '●'} {score_pct}% relevancia
    </div>
</div>
<div>{tags_html}</div>
<div class="relevance-box">💡 <b>Por qué es relevante:</b> {case.get('relevancia', 'Similitud semántica con la búsqueda')}</div>"""

    body_html = f"""<div class="field-label">🎯 Problema del cliente</div>
<div class="field-value">{case.get('problema', 'N/A')}</div>

<div class="field-label">✅ Solución implementada</div>
<div class="field-value">{case.get('solucion', 'N/A')}</div>"""

    results_html = ""
    if case.get("resultados"):
        results_html = f'<div class="results-box">📊 <b>Resultados:</b> {case["resultados"]}</div>'

    techs_html = ""
    if case.get("tecnologias"):
        techs = " ".join(f'<span class="tag-pill">{t}</span>' for t in case["tecnologias"])
        techs_html = f'<div class="field-label">🛠️ Tecnologías</div><div>{techs}</div>'

    url_html = ""
    if case.get("url_slide") and case["url_slide"] not in ("", "PENDIENTE", "None", "nan"):
        url_html = f'<div style="margin-top:0.9rem"><a href="{case["url_slide"]}" target="_blank" style="color:#58a6ff;font-size:0.85rem;text-decoration:none;">📎 Ver slide original →</a></div>'

    close_html = "</div>"

    if expanded:
        st.markdown(header_html + body_html + results_html + techs_html + url_html + close_html, unsafe_allow_html=True)
    else:
        with st.expander(f"{icon} {case.get('empresa', 'N/A')} — {case.get('industria', '')} · {score_pct}%"):
            st.markdown(header_html + body_html + results_html + techs_html + url_html + close_html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, val in {
    "results": [],
    "query": "",
    "chat_history": [],
    "chat_input": "",
    "tab": "search",
    "session_id": str(__import__('uuid').uuid4()),
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="neo-logo">⚡ NEO Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="neo-tagline">Case Search & Proposal Engine</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-label">Filtros de búsqueda</div>', unsafe_allow_html=True)
    industria = st.selectbox("🏭 Industria", INDUSTRIAS, key="sel_industria")
    area = st.selectbox("📌 Área Funcional", AREAS, key="sel_area")
    top_k = st.slider("📊 Número de resultados", 3, 10, 5, key="sel_topk")

    if st.session_state.results:
        st.markdown('<div class="section-label">Resultados de búsqueda</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-pill"><span class="stat-label">Casos encontrados</span><span class="stat-value">{len(st.session_state.results)}</span></div>', unsafe_allow_html=True)
        top = st.session_state.results[0]
        best_score = int(top["score"] * 100)
        st.markdown(f'<div class="stat-pill"><span class="stat-label">Mayor relevancia</span><span class="stat-value">{best_score}%</span></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-pill"><span class="stat-label">Mejor caso</span><span class="stat-value">{top.get("empresa", "N/A")[:18]}</span></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.results:
        if st.button("🗑️ Nueva búsqueda", use_container_width=True, key="btn_clear"):
            st.session_state.results = []
            st.session_state.query = ""
            st.session_state.chat_history = []
            st.rerun()

    st.markdown('<hr style="border-color:#21262d;margin-top:auto">', unsafe_allow_html=True)
    st.markdown('<p style="font-size:0.72rem;color:#6e7681;text-align:center">NEO Intelligence v2.0<br>Gemini + Qdrant</p>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
# ── SEARCH VIEW ──
if not st.session_state.results:
    # Hero
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1.5rem">
        <div style="font-size:2.4rem;font-weight:800;background:linear-gradient(90deg,#58a6ff,#7ee8fa,#80ff72);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-1px;margin-bottom:0.5rem">
            NEO Intelligence
        </div>
        <div style="color:#6e7681;font-size:1.05rem">
            Encuentra los mejores casos de éxito y genera propuestas de valor en segundos
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_search, col_hint = st.columns([3, 1])
    with col_search:
        query = st.text_area(
            "Describe el problema o necesidad del cliente:",
            height=130,
            placeholder="Ej: Cliente bancario necesita reducir el abandono en onboarding digital usando IA para aumentar la tasa de activación...",
            key="main_query",
        )
    with col_hint:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("💡 Mientras más específico describas el problema (industria, reto, objetivo), mejores serán los casos encontrados.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        search_btn = st.button("⚡ Buscar Casos Relevantes", type="primary", use_container_width=True, key="btn_search")
    with c2:
        st.caption("Filtros activos:")
        if industria or area:
            if industria: st.markdown(f'<span class="tag-pill tag-industry">{industria}</span>', unsafe_allow_html=True)
            if area: st.markdown(f'<span class="tag-pill tag-area">{area}</span>', unsafe_allow_html=True)
        else:
            st.caption("Ninguno")

    if search_btn:
        if not query.strip():
            st.warning("Por favor describe el problema del cliente.")
        else:
            with st.spinner("🔍 Analizando base de casos NEO..."):
                try:
                    results = call_search(query.strip(), industria, area, top_k)
                    if results:
                        st.session_state.results = results
                        st.session_state.query = query.strip()
                        st.rerun()
                    else:
                        st.info("No se encontraron casos exactos. Intenta ampliar la búsqueda o quitar los filtros.")
                except requests.exceptions.ConnectionError:
                    st.error("❌ No se pudo conectar con la API. Asegúrate de que esté corriendo:\n\n`uvicorn api:app --reload --port 8000`")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ── RESULTS + CHAT VIEW ──
else:
    results = st.session_state.results
    query = st.session_state.query

    # Header de resultados
    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem">
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#e6edf3">
                ⚡ {len(results)} caso{'s' if len(results) > 1 else ''} encontrado{'s' if len(results) > 1 else ''}
            </div>
            <div style="font-size:0.85rem;color:#6e7681;margin-top:2px">
                Búsqueda: <span style="color:#8b949e;font-style:italic">"{query[:80]}{'...' if len(query) > 80 else ''}"</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs: Casos | Chat RAG
    col_cases, col_chat = st.columns([1.1, 1.9], gap="large")

    # ── COL 1: CASOS ──
    with col_cases:
        st.markdown('<div class="section-label">📁 Casos encontrados</div>', unsafe_allow_html=True)
        for i, case in enumerate(results):
            render_case_card(i + 1, case, expanded=(i < 2))
            if i == 1 and len(results) > 2:
                st.markdown('<hr class="neo-divider">', unsafe_allow_html=True)

    # ── COL 2: CHAT RAG ──
    with col_chat:
        st.markdown('<div class="section-label">💬 Chat Inteligente</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(128,255,114,0.05);border:1px solid rgba(128,255,114,0.15);border-radius:10px;padding:0.8rem 1rem;margin-bottom:1rem">
            <span style="color:#80ff72;font-weight:600">NEO Assistant</span>
            <span style="color:#6e7681;font-size:0.88rem"> — El asistente conoce todos los casos encontrados. Pregúntale sobre ellos, pídele ideas de propuesta, o cuéntale más sobre tu cliente.</span>
        </div>
        """, unsafe_allow_html=True)

        # Quick prompts and clear
        c_qp1, c_qp2, c_clear = st.columns([2, 2, 1])
        with c_qp1:
            if st.button("💡 ¿Qué caso es el más relevante?", use_container_width=True):
                st.session_state.quick_prompt = "¿Qué caso es el más relevante y por qué?"
                st.rerun()
        with c_qp2:
            if st.button("📝 Genera un pitch", use_container_width=True):
                st.session_state.quick_prompt = "Genera un pitch de propuesta con los mejores 2 casos"
                st.rerun()
        with c_clear:
            if st.button("🗑️ Limpiar", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()

        # Render historial de chat (Native Streamlit)
        chat_container = st.container(height=450)
        with chat_container:
            if not st.session_state.chat_history:
                cases_preview = ", ".join(c.get("empresa", "N/A") for c in results[:3])
                with st.chat_message("assistant", avatar="🤖"):
                    st.write(f"Hola 👋 He analizado los **{len(results)} casos** encontrados para tu búsqueda.")
                    st.write(f"Los casos incluyen: **{cases_preview}**{'...' if len(results) > 3 else ''}.")
                    st.write("¿Qué quieres saber? Puedo explicarte cómo aplica cada caso al problema de tu cliente, ayudarte a construir una propuesta de valor, o profundizar en cualquier solución específica.")
            
            for msg in st.session_state.chat_history:
                avatar = "🧑‍💻" if msg["role"] == "user" else "🤖"
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(msg["content"])
        
        # Handle chat input
        user_msg = None
        if "quick_prompt" in st.session_state:
            user_msg = st.session_state.pop("quick_prompt")
        
        chat_input_val = st.chat_input("Escribe tu pregunta o instrucción aquí...")
        if chat_input_val:
            user_msg = chat_input_val

        if user_msg:
            st.session_state.chat_history.append({"role": "user", "content": user_msg})
            with chat_container:
                with st.chat_message("user", avatar="🧑‍💻"):
                    st.markdown(user_msg)
                with st.chat_message("assistant", avatar="🤖"):
                    with st.spinner("Pensando..."):
                        try:
                            reply = call_chat(
                                message=user_msg,
                                cases_context=results,
                                history=st.session_state.chat_history[:-1], # excluye el mensaje actual
                                session_id=st.session_state.session_id
                            )
                            st.markdown(reply)
                            st.session_state.chat_history.append({"role": "assistant", "content": reply})
                        except requests.exceptions.ConnectionError:
                            fallback = "❌ No se pudo conectar con la API. Verifica que `uvicorn` esté activo."
                            st.error(fallback)
                            st.session_state.chat_history.append({"role": "assistant", "content": fallback})
                        except requests.exceptions.HTTPError as e:
                            detail = ""
                            if e.response is not None:
                                try:
                                    detail = e.response.json().get("detail", "")
                                except Exception:
                                    detail = e.response.text
                            fallback = f"❌ Error del backend: {detail or 'fallo temporal en /chat'}"
                            st.error(fallback)
                            st.session_state.chat_history.append({"role": "assistant", "content": fallback})
                        except Exception as e:
                            fallback = f"❌ Error inesperado en chat: {e}"
                            st.error(fallback)
                            st.session_state.chat_history.append({"role": "assistant", "content": fallback})



