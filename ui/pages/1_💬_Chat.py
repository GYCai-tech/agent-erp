"""
💬 Chat con el ERP
Conversa con la base de datos en lenguaje natural usando IA
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
st.markdown("Haz preguntas sobre tus datos en lenguaje natural - **Powered by AI + MCP**")

# Verificar conexión
with st.spinner("Conectando con API..."):
    health = api_client.health_check()

if health.get("status") != "ok":
    st.error("❌ La API no está disponible. Por favor, inicia el servidor FastAPI.")
    st.stop()

# Verificar que MCP esté disponible
chat_health = api_client.check_chat_health()
if not chat_health.get("mcp_enabled"):
    st.warning("⚠️ El chat MCP no está disponible. Verifica la configuración de OpenAI API Key.")
    st.info(f"Estado: {chat_health.get('status', 'unknown')}")
    st.stop()

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# Sidebar con información y ejemplos
with st.sidebar:
    st.header("💡 Ejemplos de Preguntas")

    examples = [
        "¿Cuántas facturas tenemos en total?",
        "Muéstrame las últimas 5 facturas",
        "¿Cuáles son las tablas disponibles?",
        "¿Qué información hay en la tabla A_Facturas?",
        "¿Cuántos clientes tenemos registrados?",
        "¿Qué tablas contienen información de pedidos?",
        "Analiza la tabla de facturas",
        "¿Cuáles son las tablas con más registros?",
    ]

    st.markdown("**Prueba preguntas como:**")
    for example in examples:
        if st.button(example, key=example, use_container_width=True):
            st.session_state.example_prompt = example

    st.divider()

    # Información del modelo
    st.caption(f"🤖 Modelo: {chat_health.get('model', 'N/A')}")
    st.caption("🔧 MCP Tools: Activos")

    st.divider()

    if st.button("🗑️ Limpiar chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Mostrar herramientas usadas si las hay
        if "tools_used" in message and message["tools_used"]:
            with st.expander("🔧 Herramientas usadas"):
                for tool in message["tools_used"]:
                    st.code(f"📌 {tool['name']}", language="text")
                    if tool.get("arguments"):
                        st.json(tool["arguments"])

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

    # Generar respuesta usando MCP
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analizando tu pregunta..."):
            try:
                # Llamar al endpoint de chat
                result = api_client.chat_with_agent(
                    message=prompt,
                    conversation_history=st.session_state.conversation_history
                )

                if result.get("success"):
                    response = result.get("message", "No se pudo generar una respuesta")
                    tools_used = result.get("tools_used", [])
                    iterations = result.get("iterations", 0)

                    # Actualizar historial de conversación
                    st.session_state.conversation_history = result.get("conversation_history", [])

                    # Mostrar respuesta
                    st.markdown(response)

                    # Mostrar herramientas usadas
                    if tools_used:
                        with st.expander(f"🔧 Herramientas usadas ({len(tools_used)})"):
                            for i, tool in enumerate(tools_used, 1):
                                st.markdown(f"**{i}. {tool['name']}**")

                                if tool.get("arguments"):
                                    st.markdown("**Argumentos:**")
                                    st.json(tool["arguments"])

                                if tool.get("result"):
                                    st.markdown("**Resultado:**")
                                    result_data = tool["result"]

                                    # Mostrar resumen del resultado
                                    if isinstance(result_data, dict):
                                        if "data" in result_data and isinstance(result_data["data"], list):
                                            st.info(f"✓ {len(result_data['data'])} filas retornadas")
                                        elif "tables" in result_data and isinstance(result_data["tables"], list):
                                            st.info(f"✓ {len(result_data['tables'])} tablas encontradas")
                                        elif "error" in result_data:
                                            st.error(f"❌ Error: {result_data['error']}")
                                        else:
                                            st.json(result_data)

                                if i < len(tools_used):
                                    st.divider()

                        st.caption(f"⚡ Completado en {iterations} iteración(es)")

                    # Agregar al historial UI
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "tools_used": tools_used
                    })

                else:
                    error_msg = result.get("error", "Error desconocido")
                    st.error(f"❌ Error: {error_msg}")

                    # Agregar mensaje de error al historial
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ Lo siento, ocurrió un error: {error_msg}"
                    })

            except Exception as e:
                st.error(f"❌ Error al procesar la pregunta: {str(e)}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {str(e)}"
                })

# Nota informativa
with st.expander("ℹ️ Sobre esta funcionalidad"):
    st.markdown("""
    ### ✨ Fase 2: Chat Inteligente con MCP

    Este chat utiliza:
    - 🤖 **OpenAI GPT-4** para comprensión de lenguaje natural
    - 🔧 **MCP (Model Context Protocol)** para consultas complejas
    - 📊 **Herramientas especializadas** para la base de datos

    #### Capacidades:

    ✅ **Exploración de Base de Datos**
    - Buscar tablas por nombre
    - Ver esquema de tablas
    - Analizar relaciones entre tablas

    ✅ **Consultas SQL**
    - Genera y ejecuta consultas automáticamente
    - Solo lectura (SELECT)
    - Validación de seguridad

    ✅ **Análisis de Datos**
    - Estadísticas de tablas
    - Conteo de registros
    - Análisis de valores nulos

    #### Ejemplos de uso:

    ```
    "¿Cuántas facturas hay en total?"
    → Busca la tabla de facturas y cuenta los registros

    "Muéstrame las columnas de la tabla Clientes"
    → Busca la tabla y muestra su esquema

    "¿Qué tablas están relacionadas con pedidos?"
    → Busca y analiza las relaciones entre tablas
    ```

    #### Seguridad:

    🔒 **Solo lectura**: Solo se permiten consultas SELECT
    🛡️ **Validación**: Se bloquean operaciones peligrosas (DROP, DELETE, etc.)
    📝 **Auditoría**: Todas las consultas se registran
    """)

# Footer con estado
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.caption(f"💬 Mensajes: {len(st.session_state.messages)}")

with col2:
    st.caption(f"🤖 Modelo: {chat_health.get('model', 'N/A')}")

with col3:
    st.caption("✅ MCP Activo")
