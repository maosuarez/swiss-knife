#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                     🔪 Swiss Knife CLI                       ║
║          Navaja suiza de herramientas para WSL/Linux         ║
╚══════════════════════════════════════════════════════════════╝

Uso:
    knife <herramienta> [opciones]
    knife --list
    knife <herramienta> --help

Herramientas disponibles:
    transcribe      Transcribe audio OGG/MP3/WAV a texto
    rembg           Elimina el fondo de una imagen
    cripto	    Cifrar un mensaje
    convert	    Conversion Documentos
    clip	    Recortar Audio-Video
    find-dup	    Detectar archivos duplicados
    img-info	    Muestra metadata de imagenes
    compress	    Comprime imagenes y videos
    merge-pdf	    Une Pdfs
    fetch	    Descarga URL con texto limpio
    qr		    Generar codigos QR
"""

import sys
import argparse
import importlib
from pathlib import Path

# Windows cp1252 no puede encodear box-drawing ni emoji — forzar UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─── Registro de herramientas ─────────────────────────────────────────────────
# Añade aquí cada nueva herramienta: "nombre": ("modulo", "descripcion")
TOOLS: dict[str, tuple[str, str]] = {
    "transcribe": (
        "tools.transcribe",
        "Transcribe archivos de audio (OGG/MP3/WAV) a texto usando Google Speech",
    ),
    "rembg": (
        "tools.rembg_tool",
        "Elimina el fondo de imágenes (JPG/PNG/WEBP) con IA local",
    ),
    "crypto": (
        "tools.encryption",
        "Cifrado, descifrado y ataques (César, Vigenere, Afín, Rail Fence, Columnar, Base64)",
    ),
    "convert": (
        "tools.convert",
        "Conversión de documentos, datos, multimedia e imágenes (batch soportado)",
    ),
    "clip": (
        "tools.clip",
        "Recorta audio/video por tiempo sin pérdida de calidad (ffmpeg)",
    ),
    "find-dup": (
	"tools.find_dup", "Detecta archivos duplicados por hash"
    ),
    "img-info": ("tools.img_info", "Muestra metadata EXIF de imágenes"),
    "compress": ("tools.compress", "Comprime imágenes y videos"),
    "merge-pdf": ("tools.merge_pdf", "Une múltiples PDFs"),
    "fetch": ("tools.fetch", "Descarga una URL como texto limpio"),
    "qr": ("tools.qr", "Genera códigos QR"),
}

BANNER = """
\033[33m╔══════════════════════════════════════════════════╗
║            🔪  Swiss Knife CLI  v1.0             ║
╚══════════════════════════════════════════════════╝\033[0m
"""


def list_tools() -> None:
    print(BANNER)
    print("\033[1mHerramientas disponibles:\033[0m\n")
    for name, (_, desc) in TOOLS.items():
        print(f"  \033[36m{name:<16}\033[0m {desc}")
    print()
    print("Uso:  \033[32mknife <herramienta> --help\033[0m  para ver opciones de cada tool")
    print()


def load_tool(name: str):
    """Importa dinámicamente el módulo de la herramienta solicitada."""
    if name not in TOOLS:
        print(f"\033[31m✗ Herramienta '{name}' no encontrada.\033[0m")
        print("  Ejecuta \033[33mknife --list\033[0m para ver las disponibles.")
        sys.exit(1)

    module_path, _ = TOOLS[name]
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        print(f"\033[31m✗ Error cargando '{name}': {e}\033[0m")
        print("  Verifica que las dependencias estén instaladas en el .venv")
        sys.exit(1)


def main() -> None:
    # Sin argumentos → mostrar lista
    if len(sys.argv) == 1:
        list_tools()
        sys.exit(0)

    # --list → mostrar lista
    if sys.argv[1] in ("--list", "-l"):
        list_tools()
        sys.exit(0)

    # --version
    if sys.argv[1] in ("--version", "-v"):
        print("Swiss Knife CLI v1.0")
        sys.exit(0)

    tool_name = sys.argv[1]

    # Pasar el control + argumentos restantes a la herramienta
    # sys.argv[2:] son los argumentos propios de la tool
    sys.argv = [f"knife {tool_name}"] + sys.argv[2:]

    module = load_tool(tool_name)

    if not hasattr(module, "run"):
        print(f"\033[31m✗ El módulo '{tool_name}' no expone una función run().\033[0m")
        sys.exit(1)

    module.run()


if __name__ == "__main__":
    main()
