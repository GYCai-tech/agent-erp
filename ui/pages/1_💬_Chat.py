"""
💬 Chat con el ERP
Conversa con la base de datos en lenguaje natural
"""
import streamlit as st
import sys
from pathlib import Path

# Agregar directorio utils al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import api_client

# Configuración de la página
st.set_page_config(
    page_title="Chat ERP",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat con el ERP")
st.markdown("Haz preguntas sobre tus datos en lenguaje natural")

# Verificar conexión
with st.spinner("Conectando con API..."):
    health = api_client.health_check()

if health.get("status") != "healthy":
    st.error("❌ La API no está disponible. Por favor, inicia el servidor FastAPI.")
    st.stop()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sidebar con ejemplos
with st.sidebar:
    st.header("💡 Ejemplos de Preguntas")

    examples = [
        "¿Cuántas facturas tenemos en total?",
        "Muéstrame las últimas 5 facturas",
        "¿Cuáles son las tablas disponibles?",
        "¿Qué información hay en la tabla A_Facturas?",
        "¿Cuántos clientes tenemos registrados?",
    ]

    st.markdown("**Prueba preguntas como:**")
    for example in examples:
        if st.button(example, key=example, use_container_width=True):
            st.session_state.example_prompt = example

    st.divider()

    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Input del usuario
prompt = st.chat_input("Escribe tu pregunta aquí...")

# Si hay un ejemplo seleccionado, usarlo
if "example_prompt" in st.session_state:
    prompt = st.session_state.example_prompt
    del st.session_state.example_prompt

if prompt:
    # Agregar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            # Por ahora, respuesta simple basada en la API actual
            # En Fase 2 se integrará con MCP/OpenAI para respuestas inteligentes

            response = process_query(prompt)
            st.markdown(response)

    # Agregar respuesta al historial
    st.session_state.messages.append({"role": "assistant", "content": response})


def process_query(query: str) -> str:
    """
    Procesa la query del usuario y genera una respuesta
    Nota: Esta es una versión simplificada. En Fase 2 se integrará con LLM
    """
    query_lower = query.lower()

    # Respuestas basadas en palabras clave (simple)
    if "tabla" in query_lower and ("cuántas" in query_lower or "listar" in query_lower or "mostrar" in query_lower):
        tables = api_client.get_tables()
        if tables:
            return f"📋 Hay **{len(tables)}** tablas en la base de datos:\n\n" + "\n".join([f"- {t}" for t in tables[:10]]) + \
                   (f"\n\n...y {len(tables) - 10} más" if len(tables) > 10 else "")
        return "No se pudieron cargar las tablas"

    elif "resumen" in query_lower or "estadística" in query_lower:
        summary = api_client.get_database_summary()
        if "error" not in summary:
            return f"""📊 **Resumen de la Base de Datos:**

- **Total de tablas:** {summary.get('total_tables', 0)}
- **Tablas con datos:** {summary.get('tables_with_data', 0)}
- **Total de registros:** {summary.get('total_rows', 0):,}
"""
        return "Error al obtener el resumen"

    elif "factura" in query_lower:
        # Buscar info de la tabla A_Facturas
        table_info = api_client.get_table_info("A_Facturas")
        if "error" not in table_info:
            row_count = table_info.get('row_count', 0)
            columns = table_info.get('columns', [])

            return f"""📄 **Información de Facturas (A_Facturas):**

- **Total de facturas:** {row_count}
- **Número de campos:** {len(columns)}
- **Campos principales:** {', '.join([c['name'] for c in columns[:5]])}

Para ver más detalles, visita la página de inicio y selecciona la tabla A_Facturas.
"""
        return "No se pudo encontrar información de facturas"

    else:
        # Respuesta genérica
        return f"""🤖 Entiendo tu pregunta: "{query}"

**Nota:** Actualmente estoy en Fase 1 (exploración básica). Puedo ayudarte con:

✅ Listar tablas disponibles
✅ Mostrar resumen de la base de datos
✅ Ver información de tablas específicas

**En la Fase 2** (próximamente) podré:
- Responder preguntas complejas en lenguaje natural
- Ejecutar consultas SQL automáticamente
- Generar análisis y gráficos

💡 **Tip:** Usa la página de inicio para explorar las tablas visualmente.
"""


# Nota informativa
with st.expander("ℹ️ Sobre esta funcionalidad"):
    st.markdown("""
    ### Estado Actual: Fase 1

    Esta es una versión simplificada del chat. Actualmente responde a:
    - Preguntas sobre tablas disponibles
    - Información sobre facturas
    - Resumen de la base de datos

    ### Próximamente: Fase 2 - MCP + LLM

    En la siguiente fase se integrará:
    - 🤖 OpenAI GPT-4 para comprensión de lenguaje natural
    - 🔧 MCP (Model Context Protocol) para consultas complejas
    - 📊 Generación automática de SQL
    - 📈 Visualizaciones dinámicas
    """)
