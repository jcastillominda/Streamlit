import streamlit as st
import pypdf
import json
import io
from groq import Groq

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Revisor de CVs · UNIAJC",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Estilos personalizados ───────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Fondo */
.stApp {
    background: #0b0f1a;
    color: #dce9f7;
}

/* Header principal */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.05;
    color: #ffffff;
    margin-bottom: 0.25rem;
}
.hero-accent {
    background: linear-gradient(90deg, #34e8b0, #8bd3ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #34e8b0;
    margin-bottom: 0.5rem;
}
.hero-desc {
    font-size: 1rem;
    color: #7a9abf;
    max-width: 560px;
    line-height: 1.75;
}

/* Tarjetas de resultado */
.result-card {
    background: #0e1a2e;
    border: 1px solid rgba(139,211,255,0.15);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.score-big {
    font-family: 'Syne', sans-serif;
    font-size: 5rem;
    font-weight: 800;
    line-height: 1;
}
.score-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #7a9abf;
    margin-top: 0.5rem;
}
.tag-item {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    margin: 3px;
    font-family: 'DM Sans', sans-serif;
}
.tag-green { background: rgba(52,232,176,0.12); color: #34e8b0; border: 1px solid rgba(52,232,176,0.3); }
.tag-amber { background: rgba(245,200,66,0.12); color: #f5c842; border: 1px solid rgba(245,200,66,0.3); }
.section-title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
}

/* Botón principal */
.stButton > button {
    background: linear-gradient(135deg, #34e8b0, #8bd3ff) !important;
    color: #0b0f1a !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 2.5rem !important;
    transition: transform 0.2s, opacity 0.2s !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    opacity: 0.9 !important;
}

/* Inputs */
.stTextArea textarea, .stTextInput input {
    background: #0e1a2e !important;
    border: 1px solid rgba(139,211,255,0.2) !important;
    border-radius: 10px !important;
    color: #dce9f7 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(52,232,176,0.5) !important;
    box-shadow: 0 0 0 2px rgba(52,232,176,0.1) !important;
}

/* File uploader */
.stFileUploader {
    background: #0e1a2e !important;
    border: 1px dashed rgba(139,211,255,0.25) !important;
    border-radius: 12px !important;
}

/* Sidebar */
.css-1d391kg, [data-testid="stSidebar"] {
    background: #070d17 !important;
}

/* Separador */
hr { border-color: rgba(139,211,255,0.08) !important; }

/* Texto labels */
label, .stMarkdown p { color: #7a9abf !important; }

/* Barra de progreso personalizada */
.progress-bar-outer {
    background: rgba(139,211,255,0.08);
    border-radius: 100px;
    height: 10px;
    overflow: hidden;
    margin: 0.5rem 0 1.5rem;
}
.progress-bar-inner {
    height: 100%;
    border-radius: 100px;
    transition: width 0.8s ease;
}
</style>
""", unsafe_allow_html=True)


# ── Funciones utilitarias ────────────────────────────────────────────────────

def extraer_texto_pdf(archivo) -> str:
    """Extrae texto de un archivo PDF subido."""
    reader = pypdf.PdfReader(io.BytesIO(archivo.read()))
    texto = ""
    for pagina in reader.pages:
        texto += pagina.extract_text() or ""
    return texto.strip()


def analizar_cv(texto_cv: str, descripcion_cargo: str, api_key: str) -> dict:
    """Llama a Groq y devuelve el análisis estructurado."""
    client = Groq(api_key=api_key)

    prompt_sistema = """Eres un experto en selección de talento humano de la UNIAJC (Institución Universitaria Antonio José Camacho, Cali, Colombia).

Tu tarea es evaluar un CV comparándolo con una descripción de cargo y entregar retroalimentación constructiva y personalizada.

Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional antes ni después. El JSON debe tener exactamente esta estructura:

{
  "score": <número entero del 0 al 100>,
  "nivel": "<'Excelente' si score>=85, 'Apto' si score>=65, 'En desarrollo' si score>=40, 'No apto' si score<40>",
  "resumen": "<2-3 oraciones resumiendo el perfil del candidato y su ajuste al cargo>",
  "fortalezas": [
    {"titulo": "<nombre corto>", "detalle": "<explicación de 1-2 oraciones>"},
    {"titulo": "<nombre corto>", "detalle": "<explicación de 1-2 oraciones>"},
    {"titulo": "<nombre corto>", "detalle": "<explicación de 1-2 oraciones>"}
  ],
  "mejoras": [
    {"titulo": "<área a mejorar>", "sugerencia": "<acción concreta y específica>"},
    {"titulo": "<área a mejorar>", "sugerencia": "<acción concreta y específica>"},
    {"titulo": "<área a mejorar>", "sugerencia": "<acción concreta y específica>"}
  ],
  "palabras_clave_faltantes": ["<keyword1>", "<keyword2>", "<keyword3>"]
}"""

    prompt_usuario = f"""CV DEL CANDIDATO:
{texto_cv}

DESCRIPCIÓN DEL CARGO:
{descripcion_cargo}"""

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ],
        max_tokens=1500,
        temperature=0.3,
    )

    texto_respuesta = respuesta.choices[0].message.content.strip()

    # Limpiar posibles backticks de markdown
    if texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta.split("```")[1]
        if texto_respuesta.startswith("json"):
            texto_respuesta = texto_respuesta[4:]

    return json.loads(texto_respuesta)


def color_score(score: int) -> str:
    if score >= 85:
        return "#34e8b0"
    elif score >= 65:
        return "#8bd3ff"
    elif score >= 40:
        return "#f5c842"
    else:
        return "#ff6b6b"


def barra_progreso(score: int) -> str:
    color = color_score(score)
    return f"""
<div class="progress-bar-outer">
  <div class="progress-bar-inner" style="width:{score}%; background: linear-gradient(90deg, {color}aa, {color});"></div>
</div>
"""


# ── Layout principal ─────────────────────────────────────────────────────────

# Header
st.markdown('<p class="hero-sub">🎓 UNIAJC · Bolsa de Empleo</p>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Revisor de CVs <span class="hero-accent">con IA</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-desc">Sube un CV en PDF, ingresa la descripción del cargo y obtén un análisis detallado con sugerencias personalizadas en segundos.</p>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Sidebar: configuración ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("---")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="Obtén tu key gratis en console.groq.com"
    )
    st.markdown("""
    <small style='color:#344860; font-size:0.75rem;'>
    🔒 Tu key solo se usa en esta sesión y nunca se guarda.
    <br><br>
    📖 <a href='https://console.groq.com' target='_blank' style='color:#34e8b0;'>Obtener API Key gratis →</a>
    </small>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("""
    <small style='color:#344860; font-size:0.75rem;'>
    <b style='color:#7a9abf;'>Modelo:</b> llama-3.1-70b (Groq)<br>
    <b style='color:#7a9abf;'>Versión:</b> 1.0.0<br>
    <b style='color:#7a9abf;'>Desarrollado para:</b> UNIAJC
    </small>
    """, unsafe_allow_html=True)

# ── Formulario principal ─────────────────────────────────────────────────────
col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.markdown("#### 📄 CV del candidato")
    archivo_cv = st.file_uploader(
        "Arrastra el PDF aquí o haz clic para buscarlo",
        type=["pdf"],
        label_visibility="collapsed"
    )
    if archivo_cv:
        st.success(f"✓ Archivo cargado: **{archivo_cv.name}**")

with col_der:
    st.markdown("#### 💼 Descripción del cargo")
    descripcion_cargo = st.text_area(
        "Pega aquí la descripción del cargo",
        height=200,
        placeholder="Ejemplo:\n\nDesarrollador Full Stack\n\nBuscamos profesional con experiencia en React y Node.js, mínimo 2 años de experiencia, conocimientos en bases de datos SQL...",
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Botón de análisis
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    analizar = st.button("🔍 Analizar CV", use_container_width=True)

st.markdown("---")

# ── Lógica de análisis ───────────────────────────────────────────────────────
if analizar:
    # Validaciones
    if not api_key:
        st.error("⚠️ Ingresa tu Groq API Key en el panel izquierdo.")
        st.stop()
    if not archivo_cv:
        st.error("⚠️ Por favor sube el CV en formato PDF.")
        st.stop()
    if not descripcion_cargo.strip():
        st.error("⚠️ Por favor ingresa la descripción del cargo.")
        st.stop()

    with st.spinner("Extrayendo texto del CV..."):
        try:
            texto_cv = extraer_texto_pdf(archivo_cv)
        except Exception as e:
            st.error(f"Error al leer el PDF: {e}")
            st.stop()

    if len(texto_cv) < 100:
        st.warning("⚠️ El PDF parece estar escaneado como imagen. Prueba con un PDF con texto seleccionable.")
        st.stop()

    with st.spinner("Analizando con IA... esto toma unos segundos ✨"):
        try:
            resultado = analizar_cv(texto_cv, descripcion_cargo, api_key)
        except json.JSONDecodeError:
            st.error("El modelo devolvió una respuesta inesperada. Intenta de nuevo.")
            st.stop()
        except Exception as e:
            st.error(f"Error al conectar con Groq: {e}")
            st.stop()

    # ── MOSTRAR RESULTADOS ────────────────────────────────────────────────────
    score = resultado.get("score", 0)
    nivel = resultado.get("nivel", "—")
    resumen = resultado.get("resumen", "")
    fortalezas = resultado.get("fortalezas", [])
    mejoras = resultado.get("mejoras", [])
    keywords = resultado.get("palabras_clave_faltantes", [])
    color = color_score(score)

    st.markdown("## 📊 Resultado del análisis")
    st.markdown("<br>", unsafe_allow_html=True)

    # Fila superior: score + resumen
    col_score, col_resumen = st.columns([1, 2], gap="large")

    with col_score:
        st.markdown(f"""
        <div class="result-card" style="text-align:center; border-top: 3px solid {color};">
            <div class="score-big" style="color:{color};">{score}</div>
            <div class="score-label">Puntuación / 100</div>
            <br>
            <span class="tag-item" style="background:{color}22; color:{color}; border:1px solid {color}55; font-size:1rem; font-family:'Syne',sans-serif; font-weight:700;">
                {nivel}
            </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(barra_progreso(score), unsafe_allow_html=True)

    with col_resumen:
        st.markdown(f"""
        <div class="result-card" style="height:100%;">
            <div class="section-title" style="color:{color};">📝 Resumen del perfil</div>
            <p style="color:#dce9f7; font-size:0.95rem; line-height:1.8;">{resumen}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Fortalezas y mejoras
    col_fort, col_mej = st.columns(2, gap="large")

    with col_fort:
        items_html = ""
        for f in fortalezas:
            items_html += f"""
            <div style="margin-bottom:1rem; padding:0.85rem; background:rgba(52,232,176,0.05); border-left:3px solid #34e8b0; border-radius:0 8px 8px 0;">
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#34e8b0; font-size:0.9rem;">✓ {f.get('titulo','')}</div>
                <div style="color:#7a9abf; font-size:0.85rem; margin-top:0.3rem; line-height:1.6;">{f.get('detalle','')}</div>
            </div>"""
        st.markdown(f"""
        <div class="result-card">
            <div class="section-title" style="color:#34e8b0;">💪 Fortalezas detectadas</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

    with col_mej:
        items_html = ""
        for m in mejoras:
            items_html += f"""
            <div style="margin-bottom:1rem; padding:0.85rem; background:rgba(245,200,66,0.05); border-left:3px solid #f5c842; border-radius:0 8px 8px 0;">
                <div style="font-family:'Syne',sans-serif; font-weight:700; color:#f5c842; font-size:0.9rem;">→ {m.get('titulo','')}</div>
                <div style="color:#7a9abf; font-size:0.85rem; margin-top:0.3rem; line-height:1.6;">{m.get('sugerencia','')}</div>
            </div>"""
        st.markdown(f"""
        <div class="result-card">
            <div class="section-title" style="color:#f5c842;">🎯 Áreas de mejora</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

    # Keywords faltantes
    if keywords:
        tags_html = "".join(
            f'<span class="tag-item tag-amber">+ {kw}</span>' for kw in keywords
        )
        st.markdown(f"""
        <div class="result-card">
            <div class="section-title" style="color:#8bd3ff; margin-bottom:0.5rem;">🔑 Palabras clave a incluir en el CV</div>
            <p style="color:#344860; font-size:0.8rem; margin-bottom:0.75rem;">Estos términos aparecen en el cargo pero no en el CV. Inclúyelos si aplican a tu experiencia real.</p>
            <div>{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # Tip final
    if score < 65:
        st.info("💡 **Tip:** Un score bajo no significa que el candidato no sea válido — solo que el CV necesita más alineación con el cargo. Las sugerencias anteriores son el punto de partida.")
    elif score >= 85:
        st.success("🎉 ¡Excelente perfil! Este candidato tiene un ajuste muy alto con el cargo descrito.")
