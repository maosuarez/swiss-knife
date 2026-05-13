"""
🖼️ rembg — Eliminación de fondo de imágenes
═══════════════════════════════════════════════════════════════
Elimina el fondo de imágenes usando el modelo U2Net (local, sin API).

Formatos entrada:   JPG · PNG · WEBP · BMP
Formato salida:     PNG (preserva transparencia)
Modelos:            u2net (default), u2net_human_seg, isnet-general-use

Ejemplos:
    knife rembg foto.jpg
    knife rembg foto.jpg --output sin_fondo.png
    knife rembg foto.jpg --model u2net_human_seg
    knife rembg *.jpg --batch
═══════════════════════════════════════════════════════════════
"""

import sys
import argparse
from pathlib import Path


def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        sys.exit(1)


SUPPORTED_INPUT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MODELS = {
    "u2net": "Modelo general (recomendado)",
    "u2net_human_seg": "Optimizado para personas",
    "isnet-general-use": "Alta precisión, más lento",
}


def remove_background(input_path: Path, output_path: Path, model_name: str) -> None:
    rembg = _require("rembg", "rembg[cpu]")
    PIL = _require("PIL", "Pillow")
    Image = PIL.Image

    session = rembg.new_session(model_name)
    img = Image.open(input_path)
    result = rembg.remove(img, session=session)
    result.save(output_path, format="PNG")


def process_file(input_path: Path, output_path: Path | None, model: str) -> Path:
    if input_path.suffix.lower() not in SUPPORTED_INPUT:
        print(f"\033[31m✗ Formato no soportado: {input_path.suffix}\033[0m")
        print(f"  Formatos válidos: {', '.join(SUPPORTED_INPUT)}")
        sys.exit(1)

    if output_path is None:
        output_path = input_path.with_stem(input_path.stem + "_nobg").with_suffix(".png")

    print(f"\033[33m⏳ Procesando:\033[0m {input_path.name}  [modelo: {model}]")
    remove_background(input_path, output_path, model)
    print(f"\033[32m✓ Guardado:\033[0m {output_path.resolve()}\n")
    return output_path


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife rembg",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "images",
        nargs="+",
        help="Imagen(es) de entrada",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Archivo de salida (solo válido con una imagen)",
    )
    parser.add_argument(
        "--model", "-m",
        default="u2net",
        choices=list(MODELS.keys()),
        help=f"Modelo a usar (default: u2net)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="Muestra los modelos disponibles",
    )

    args = parser.parse_args()

    if args.list_models:
        print("\n\033[1mModelos disponibles:\033[0m\n")
        for m, desc in MODELS.items():
            mark = " \033[32m← default\033[0m" if m == "u2net" else ""
            print(f"  \033[36m{m:<28}\033[0m {desc}{mark}")
        print()
        return

    images = [Path(p) for p in args.images]

    if args.output and len(images) > 1:
        print("\033[31m✗ --output solo puede usarse con una imagen a la vez.\033[0m")
        sys.exit(1)

    for img_path in images:
        if not img_path.exists():
            print(f"\033[33m⚠ No encontrado, saltando: {img_path}\033[0m")
            continue
        out = Path(args.output) if args.output else None
        process_file(img_path, out, args.model)
