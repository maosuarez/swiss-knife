"""
🛠️ TEMPLATE — Nueva herramienta para Swiss Knife
═══════════════════════════════════════════════════════════════
Instrucciones:
  1. Copia este archivo como tools/<nombre>.py
  2. Agrega la entrada en el dict TOOLS de main.py:
       "nombre": ("tools.<nombre>", "descripción corta"),
  3. Agrega dependencias a requirements.txt si es necesario.
  4. Implementa la lógica en run().

El contrato mínimo es: exponer una función run() sin argumentos.
Los argumentos CLI se leen via argparse desde sys.argv.
═══════════════════════════════════════════════════════════════

🔧 mytool — Descripción de una línea
═══════════════════════════════════════════════════════════════
Descripción extendida de qué hace la herramienta.

Ejemplos:
    knife mytool input.txt
    knife mytool archivo --opcion valor
═══════════════════════════════════════════════════════════════
"""

import sys
import argparse
from pathlib import Path


# ─── Helper opcional para imports con mensaje de error claro ──────────────────
def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        # Para conda-forge packages, usa "conda install -c conda-forge {pip_name}"
        # Para pip packages, usa "pip install {pip_name}"
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        sys.exit(1)


# ─── Lógica principal ─────────────────────────────────────────────────────────

def do_something(input_path: Path, option: str) -> str:
    """Implementa aquí la lógica core de la herramienta."""
    # Importar dependencias aquí (tardíamente)
    # lib = _require("alguna_lib")
    raise NotImplementedError("Implementa esta función")


# ─── Punto de entrada del CLI ─────────────────────────────────────────────────

def run() -> None:
    # Importar Rich localmente para output visual
    # from rich.console import Console
    # console = Console()
    parser = argparse.ArgumentParser(
        prog="knife mytool",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Argumentos posicionales
    parser.add_argument(
        "input",
        help="Archivo o ruta de entrada",
    )

    # Flags opcionales
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Archivo de salida (opcional)",
    )
    parser.add_argument(
        "--option",
        default="default_value",
        help="Alguna opción configurable (default: default_value)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada del proceso",
    )

    args = parser.parse_args()

    # Validaciones
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\033[31m✗ Archivo no encontrado: {input_path}\033[0m")
        sys.exit(1)

    # Ejecución
    # Ejemplo con Rich (reemplaza los print() con colores ANSI):
    # console.print(f"⏳ Procesando: {input_path.name}", style="yellow")
    print(f"\033[33m⏳ Procesando:\033[0m {input_path.name}")

    result = do_something(input_path, args.option)

    # Output
    # console.print(f"✓ Resultado: {result}", style="green")
    print(f"\033[32m✓ Resultado:\033[0m {result}")

    if args.output:
        out = Path(args.output)
        out.write_text(result, encoding="utf-8")
        # console.print(f"💾 Guardado en: {out.resolve()}", style="cyan")
        print(f"\033[36m💾 Guardado en: {out.resolve()}\033[0m")
