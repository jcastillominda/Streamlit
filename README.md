# 💼 Revisor de CVs con IA — UNIAJC

Agente inteligente que analiza CVs en PDF, los compara contra descripciones de cargo y genera retroalimentación personalizada. Desarrollado para la Bolsa de Empleo de la UNIAJC.

## 🚀 Despliegue en Streamlit Cloud (gratis, sin servidor)

### Paso 1 — Sube el proyecto a GitHub
1. Crea un repositorio nuevo en [github.com](https://github.com) (puede ser privado)
2. Sube los dos archivos: `app.py` y `requirements.txt`

### Paso 2 — Despliega en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub
2. Clic en **"New app"**
3. Selecciona tu repositorio y la rama `main`
4. En **"Main file path"** escribe: `app.py`
5. Clic en **"Deploy"** — listo en ~2 minutos

### Paso 3 — Obtén tu Groq API Key (gratis)
1. Entra a [console.groq.com](https://console.groq.com)
2. Regístrate con Gmail (sin tarjeta de crédito)
3. Ve a **API Keys → Create API Key**
4. Copia la key (formato `gsk_...`)
5. Pégala en el panel lateral de la app al usarla

## 🏃 Prueba local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la app
streamlit run app.py
```

## 📁 Estructura del proyecto

```
revisor-cvs/
├── app.py           ← Aplicación principal
├── requirements.txt ← Dependencias Python
└── README.md        ← Este archivo
```

## ⚙️ Cómo funciona

1. El usuario sube un CV en PDF
2. `pypdf` extrae el texto del documento
3. Se construye un prompt con el CV + la descripción del cargo
4. Se llama a la API de Groq (modelo `llama-3.1-70b-versatile`)
5. El modelo devuelve un JSON con: score, nivel, fortalezas, mejoras y keywords faltantes
6. Streamlit renderiza el resultado con visualización de colores según el score

## 🔒 Seguridad
- La API Key **nunca se guarda** — solo vive en la sesión del navegador
- No se almacena ningún CV ni dato personal
- Para producción, considera usar `st.secrets` de Streamlit para manejar la key

## 📌 Personalización
- Cambia el modelo en `app.py` → línea con `model="llama-3.1-70b-versatile"` (también puedes usar `gemma2-9b-it` o `mixtral-8x7b-32768`)
- Modifica el `prompt_sistema` para ajustar los criterios de evaluación al contexto de la UNIAJC
- Agrega un nodo de Google Sheets con `gspread` para guardar el historial de análisis
