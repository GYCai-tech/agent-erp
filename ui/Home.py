"""
🏠 Dashboard Principal - Agente ERP
Interfaz simple para explorar y consultar la base de datos del ERP
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Agregar directorio utils al path
sys.path.insert(0, str(Path(__file__).parent))

from utils.api_client import api_client

# Configuración de la página
st.set_page_config(
    page_title="Agente ERP - Gómez y Crespo",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🏢 Agente ERP - Gómez y Crespo")
st.markdown("Sistema inteligente de consultas a la base de datos ERP")

# Sidebar con info
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Desarrollado por:** Santiago Arce

    **Empresa:** Gómez y Crespo, Ourense

    **Versión:** 1.0.0 (Fase 1)
    """)

    st.divider()

    # Health check
    with st.spinner("Conectando con API..."):
        health = api_client.health_check()

    if health.get("status") == "healthy":
        st.success("✅ API conectada")
        st.caption(f"Base de datos: {health.get('database', 'N/A')}")
    else:
        st.error("❌ API desconectada")
        st.caption("Verifica que FastAPI esté ejecutándose")

# Verificar conexión antes de continuar
if health.get("status") != "healthy":
    st.warning("⚠️ La API no está disponible. Por favor, inicia el servidor FastAPI:")
    st.code("cd P:/agente-erp\npython app/main.py", language="bash")
    st.stop()

# Resumen de la base de datos
st.header("📊 Resumen de la Base de Datos")

with st.spinner("Cargando resumen..."):
    summary = api_client.get_database_summary()

if "error" not in summary:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📋 Total de Tablas",
            value=summary.get("total_tables", 0)
        )

    with col2:
        st.metric(
            label="📊 Tablas con Datos",
            value=summary.get("tables_with_data", 0)
        )

    with col3:
        total_rows = summary.get("total_rows", 0)
        st.metric(
            label="📈 Total de Registros",
            value=f"{total_rows:,}".replace(",", ".")
        )
else:
    st.error(f"Error al cargar resumen: {summary.get('error')}")

st.divider()

# Explorador de tablas
st.header("🔍 Explorador de Tablas")

# Búsqueda de tablas
col1, col2 = st.columns([3, 1])

with col1:
    search_term = st.text_input(
        "Buscar tablas",
        placeholder="Ejemplo: facturas, clientes, ventas...",
        help="Busca tablas por nombre"
    )

with col2:
    st.write("")  # Espaciado
    st.write("")  # Espaciado
    search_button = st.button("🔎 Buscar", use_container_width=True)

# Cargar tablas
if search_term and search_button:
    with st.spinner(f"Buscando '{search_term}'..."):
        tables = api_client.search_tables(search_term)
else:
    with st.spinner("Cargando tablas..."):
        tables = api_client.get_tables()

if tables:
    # Selector de tabla
    selected_table = st.selectbox(
        "Selecciona una tabla para ver detalles",
        options=tables,
        index=0
    )

    if selected_table:
        # Tabs para organizar información
        tab1, tab2 = st.tabs(["📋 Información", "📊 Vista Previa de Datos"])

        with tab1:
            with st.spinner(f"Cargando información de {selected_table}..."):
                table_info = api_client.get_table_info(selected_table)

            if "error" not in table_info:
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader(f"Tabla: {table_info['name']}")

                with col2:
                    row_count = table_info.get('row_count', 0)
                    st.metric("Registros", f"{row_count:,}".replace(",", "."))

                # Primary Keys
                if table_info.get('primary_keys'):
                    st.write("**🔑 Primary Keys:**", ", ".join(table_info['primary_keys']))

                # Columnas
                st.write("**📋 Columnas:**")

                columns_data = []
                for col in table_info.get('columns', []):
                    columns_data.append({
                        "Columna": col['name'],
                        "Tipo": col['type'],
                        "Nullable": "Sí" if col['nullable'] else "No",
                        "Autoincrement": "Sí" if col.get('autoincrement') else "No"
                    })

                if columns_data:
                    df_columns = pd.DataFrame(columns_data)
                    st.dataframe(df_columns, use_container_width=True, hide_index=True)

                # Foreign Keys
                if table_info.get('foreign_keys'):
                    st.write("**🔗 Relaciones (Foreign Keys):**")
                    for fk in table_info['foreign_keys']:
                        constrained = ', '.join(fk['constrained_columns'])
                        referred = ', '.join(fk['referred_columns'])
                        st.write(f"- {constrained} → {fk['referred_table']}.{referred}")
            else:
                st.error(f"Error: {table_info.get('error')}")

        with tab2:
            # Límite de registros
            limit = st.slider("Número de registros", min_value=5, max_value=50, value=10, step=5)

            with st.spinner(f"Cargando muestra de {selected_table}..."):
                sample = api_client.get_table_sample(selected_table, limit=limit)

            if "error" not in sample and sample.get('data'):
                df_sample = pd.DataFrame(sample['data'])
                st.dataframe(df_sample, use_container_width=True, hide_index=True)

                st.caption(f"Mostrando {len(sample['data'])} de {sample.get('total_rows', 0)} registros totales")
            elif "error" in sample:
                st.error(f"Error: {sample.get('error')}")
            else:
                st.info("No hay datos disponibles para esta tabla")
else:
    st.info("No se encontraron tablas")

# Footer
st.divider()
st.caption("💡 **Tip:** Usa la página 💬 Chat para hacer consultas en lenguaje natural a la base de datos")
