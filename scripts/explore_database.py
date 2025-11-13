"""
Script para explorar la estructura de la base de datos
Genera documentación automática en formato Markdown
"""
import sys
from pathlib import Path

# Agregar directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.database.explorer import db_explorer
from app.core.logging import setup_logging
from datetime import datetime


def generate_markdown_documentation(output_file: str = "docs/database_schema.md"):
    """
    Genera documentación completa de la base de datos en Markdown

    Args:
        output_file: Ruta del archivo de salida
    """
    logger = setup_logging("explore_database")

    logger.info("=" * 80)
    logger.info("EXPLORADOR DE BASE DE DATOS")
    logger.info("=" * 80)

    try:
        # Obtener información de todas las tablas
        logger.info("\nObteniendo información de todas las tablas...")
        tables_info = db_explorer.get_all_tables_info()

        # Generar resumen
        summary = db_explorer.get_database_summary()

        # Crear contenido Markdown
        md_content = []

        # Encabezado
        md_content.append("# Documentación de Base de Datos - ERP")
        md_content.append("")
        md_content.append(f"**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append("")

        # Resumen
        md_content.append("## 📊 Resumen General")
        md_content.append("")
        md_content.append(f"- **Total de tablas**: {summary['total_tables']}")
        md_content.append(f"- **Tablas con datos**: {summary['tables_with_data']}")
        md_content.append(f"- **Total de filas**: {summary['total_rows']:,}")
        md_content.append("")

        # Índice de tablas
        md_content.append("## 📑 Índice de Tablas")
        md_content.append("")
        for table in tables_info:
            md_content.append(f"- [{table['name']}](#{table['name'].lower().replace('_', '-')})")
        md_content.append("")
        md_content.append("---")
        md_content.append("")

        # Detalles de cada tabla
        md_content.append("## 📋 Detalle de Tablas")
        md_content.append("")

        for table in tables_info:
            logger.info(f"  Documentando tabla: {table['name']}")

            md_content.append(f"### {table['name']}")
            md_content.append("")

            # Información básica
            row_count = table.get('row_count', 'N/A')
            md_content.append(f"**Número de filas**: {row_count:,}" if isinstance(row_count, int) else f"**Número de filas**: {row_count}")
            md_content.append("")

            # Primary Keys
            if table['primary_keys']:
                md_content.append(f"**Primary Key(s)**: {', '.join(table['primary_keys'])}")
                md_content.append("")

            # Columnas
            md_content.append("#### Columnas")
            md_content.append("")
            md_content.append("| Columna | Tipo | Nullable | Default | Autoincrement |")
            md_content.append("|---------|------|----------|---------|---------------|")

            for col in table['columns']:
                nullable = "Sí" if col['nullable'] else "No"
                default = col['default'] if col['default'] else "-"
                auto = "Sí" if col['autoincrement'] else "No"
                md_content.append(f"| {col['name']} | {col['type']} | {nullable} | {default} | {auto} |")

            md_content.append("")

            # Foreign Keys
            if table['foreign_keys']:
                md_content.append("#### Relaciones (Foreign Keys)")
                md_content.append("")

                for fk in table['foreign_keys']:
                    constrained = ', '.join(fk['constrained_columns'])
                    referred = ', '.join(fk['referred_columns'])
                    md_content.append(f"- **{constrained}** → {fk['referred_table']}.{referred}")

                md_content.append("")

            md_content.append("---")
            md_content.append("")

        # Guardar archivo
        output_path = Path(root_dir) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_content))

        logger.info("")
        logger.info("=" * 80)
        logger.info("✓ EXPLORACIÓN COMPLETADA")
        logger.info("=" * 80)
        logger.info(f"  Tablas documentadas: {len(tables_info)}")
        logger.info(f"  Archivo generado: {output_path}")
        logger.info("=" * 80)

        return True

    except Exception as e:
        logger.error(f"✗ Error durante la exploración: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal"""
    success = generate_markdown_documentation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
