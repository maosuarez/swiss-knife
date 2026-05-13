"""
🔄 convert — Conversor multipropósito
═══════════════════════════════════════════════════════════════
DOCUMENTOS
  pdf2docx      PDF → DOCX (reconstrucción editable)
  docx/pptx/xlsx/odt → pdf | odt | txt   (LibreOffice)
  pdf → txt     Extrae texto plano

DATOS ESTRUCTURADOS
  csv  ↔ json
  json ↔ yaml

WEB / TEXTO
  md  ↔ html    (pandoc)

AUDIO
  ogg | mp3 | wav | flac | m4a | aac  →  mp3 | wav | ogg | flac
  mpeg audio (.mpeg / .mpga)          →  mp3

VIDEO
  mp4 | mkv | avi | mov | webm  →  mp4 | mkv | avi | mov
  video → mp3                        Extrae solo el audio

Ejemplos:
    knife convert audio.mpeg --to mp3
    knife convert video.mp4 --to mp3
    knife convert video.mp4 --to audio           # alias de --to mp3
    knife convert video.mkv --to mp4
    knife convert documento.pdf --to docx
    knife convert datos.csv --to json
    knife convert carpeta/ --to mp3 --batch
═══════════════════════════════════════════════════════════════
"""

import sys
import argparse
import subprocess
import shutil
import json
import csv
from pathlib import Path

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        sys.exit(1)


def _require_binary(name: str, install_hint: str | None = None):
    if not shutil.which(name):
        hint = install_hint or f"sudo apt install {name}"
        print(f"\033[31m✗ Falta binario: '{name}'\033[0m")
        print(f"  Instala con:  {hint}")
        sys.exit(1)


def _run(cmd: list[str], verbose: bool = False) -> None:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if not verbose else None,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.decode())
        sys.exit(1)


# ─── Clasificación de formatos ────────────────────────────────────────────────

AUDIO_FORMATS  = {"ogg", "mp3", "wav", "flac", "m4a", "aac", "mpeg", "mpga", "opus", "weba"}
VIDEO_FORMATS  = {"mp4", "mkv", "avi", "mov", "webm", "flv", "ts", "m4v"}
AUDIO_TARGETS  = {"mp3", "wav", "ogg", "flac", "aac"}
VIDEO_TARGETS  = {"mp4", "mkv", "avi", "mov", "webm"}

def _is_audio(ext: str) -> bool:
    return ext in AUDIO_FORMATS

def _is_video(ext: str) -> bool:
    return ext in VIDEO_FORMATS


# ─── Conversores específicos ──────────────────────────────────────────────────

def _convert_audio(input_path: Path, to: str, output: Path, bitrate: str, verbose: bool) -> Path:
    """Audio → Audio usando ffmpeg."""
    _require_binary("ffmpeg", "sudo apt install ffmpeg")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vn",                        # descartar video si lo hubiera
        "-ab", bitrate,               # bitrate de audio
        str(output),
    ]
    if not verbose:
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-i", str(input_path), "-vn", "-ab", bitrate, str(output)]
    _run(cmd, verbose=verbose)
    return output


def _convert_video_to_audio(input_path: Path, output: Path, bitrate: str, verbose: bool) -> Path:
    """Video → MP3 (u otro formato de audio): extrae solo el stream de audio."""
    _require_binary("ffmpeg", "sudo apt install ffmpeg")
    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "error" if not verbose else "info",
        "-i", str(input_path),
        "-vn",
        "-acodec", "libmp3lame" if output.suffix == ".mp3" else "copy",
        "-ab", bitrate,
        str(output),
    ]
    _run(cmd, verbose=verbose)
    return output


def _convert_video(input_path: Path, output: Path, quality: str, verbose: bool) -> Path:
    """Video → Video usando ffmpeg con reencoding o stream copy."""
    _require_binary("ffmpeg", "sudo apt install ffmpeg")

    # CRF por perfil de calidad
    crf_map = {"high": "18", "medium": "23", "low": "28"}
    crf = crf_map.get(quality, "23")

    cmd = [
        "ffmpeg", "-y",
        "-loglevel", "error" if not verbose else "info",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", crf,
        "-c:a", "aac",
        "-b:a", "192k",
        str(output),
    ]
    _run(cmd, verbose=verbose)
    return output


def _convert_pdf_to_docx(input_path: Path, output: Path) -> Path:
    from pdf2docx import Converter
    _require("pdf2docx")
    cv = Converter(str(input_path))
    cv.convert(str(output))
    cv.close()
    return output


def _convert_pdf_to_txt(input_path: Path, output: Path) -> Path:
    pdfminer = _require("pdfminer.high_level", "pdfminer.six")
    from pdfminer.high_level import extract_text
    text = extract_text(str(input_path))
    output.write_text(text, encoding="utf-8")
    return output


def _convert_office(input_path: Path, to: str, output: Path) -> Path:
    _require_binary("libreoffice")
    _run([
        "libreoffice", "--headless",
        "--convert-to", to,
        str(input_path),
        "--outdir", str(input_path.parent),
    ])
    return output


def _convert_csv_json(input_path: Path, output: Path) -> Path:
    with open(input_path, newline='', encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


def _convert_json_csv(input_path: Path, output: Path) -> Path:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    with open(output, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    return output


def _convert_json_yaml(input_path: Path, output: Path) -> Path:
    yaml = _require("yaml", "pyyaml")
    data = json.loads(input_path.read_text(encoding="utf-8"))
    output.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return output


def _convert_yaml_json(input_path: Path, output: Path) -> Path:
    yaml = _require("yaml", "pyyaml")
    data = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    output.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return output


def _convert_markup(input_path: Path, output: Path) -> Path:
    _require_binary("pandoc")
    _run(["pandoc", str(input_path), "-o", str(output)])
    return output


# ─── Dispatcher central ───────────────────────────────────────────────────────

def convert(input_path: Path, to: str, args) -> Path:
    src = input_path.suffix.lower().lstrip(".")

    # Alias: --to audio → --to mp3
    if to == "audio":
        to = "mp3"

    output = input_path.with_suffix(f".{to}")

    # ── Audio → Audio (incluye mpeg/mpga → mp3) ──────────────────────────────
    if _is_audio(src) and to in AUDIO_TARGETS:
        return _convert_audio(input_path, to, output, args.bitrate, args.verbose)

    # ── Video → Audio (extrae audio) ─────────────────────────────────────────
    if _is_video(src) and to in AUDIO_TARGETS:
        return _convert_video_to_audio(input_path, output, args.bitrate, args.verbose)

    # ── Video → Video ────────────────────────────────────────────────────────
    if _is_video(src) and to in VIDEO_TARGETS:
        return _convert_video(input_path, output, args.quality, args.verbose)

    # ── PDF → DOCX ───────────────────────────────────────────────────────────
    if src == "pdf" and to == "docx":
        return _convert_pdf_to_docx(input_path, output)

    # ── PDF → TXT ────────────────────────────────────────────────────────────
    if src == "pdf" and to == "txt":
        return _convert_pdf_to_txt(input_path, output)

    # ── Office → PDF/ODT/TXT ─────────────────────────────────────────────────
    if src in {"docx", "pptx", "xlsx", "odt"} and to in {"pdf", "odt", "txt"}:
        return _convert_office(input_path, to, output)

    # ── CSV ↔ JSON ────────────────────────────────────────────────────────────
    if src == "csv" and to == "json":
        return _convert_csv_json(input_path, output)
    if src == "json" and to == "csv":
        return _convert_json_csv(input_path, output)

    # ── JSON ↔ YAML ───────────────────────────────────────────────────────────
    if src == "json" and to == "yaml":
        return _convert_json_yaml(input_path, output)
    if src in {"yaml", "yml"} and to == "json":
        return _convert_yaml_json(input_path, output)

    # ── Markup (MD ↔ HTML) ────────────────────────────────────────────────────
    if src in {"md", "html"} and to in {"md", "html"}:
        return _convert_markup(input_path, output)

    print(f"\033[31m✗ Conversión no soportada: {src} → {to}\033[0m")
    print("  Ejecuta \033[33mknife convert --formats\033[0m para ver combinaciones válidas.")
    sys.exit(1)


# ─── CLI ──────────────────────────────────────────────────────────────────────

FORMATS_HELP = """
┌─────────────────┬─────────────────────────────────────────┐
│ ORIGEN          │ DESTINOS                                │
├─────────────────┼─────────────────────────────────────────┤
│ mpeg/mpga       │ mp3                                     │
│ ogg/mp3/wav/... │ mp3 · wav · ogg · flac · aac            │
│ mp4/mkv/avi/... │ mp3 · wav  (extrae audio)               │
│ mp4/mkv/avi/... │ mp4 · mkv · avi · mov · webm            │
│ pdf             │ docx · txt                              │
│ docx/pptx/xlsx  │ pdf · odt · txt                         │
│ csv             │ json                                    │
│ json            │ csv · yaml                              │
│ yaml/yml        │ json                                    │
│ md              │ html                                    │
│ html            │ md                                      │
└─────────────────┴─────────────────────────────────────────┘
"""


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife convert",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", nargs="?", help="Archivo o carpeta de entrada")
    parser.add_argument(
        "--to", metavar="FORMAT",
        help="Formato destino (ej: mp3, mp4, docx, json). Usa 'audio' como alias de mp3.",
    )
    parser.add_argument(
        "--batch", action="store_true",
        help="Procesar todos los archivos de una carpeta",
    )
    parser.add_argument(
        "--bitrate", default="192k", metavar="BITRATE",
        help="Bitrate para conversiones de audio (default: 192k). Ej: 128k, 320k",
    )
    parser.add_argument(
        "--quality", default="medium", choices=["high", "medium", "low"],
        help="Calidad para conversiones de video (default: medium)",
    )
    parser.add_argument(
        "--formats", action="store_true",
        help="Muestra tabla de conversiones soportadas",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    if args.formats:
        print(FORMATS_HELP)
        return

    if not args.input or not args.to:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\033[31m✗ No existe: {input_path}\033[0m")
        sys.exit(1)

    files: list[Path] = (
        [f for f in input_path.iterdir() if f.is_file()]
        if args.batch and input_path.is_dir()
        else [input_path]
    )

    errored = 0
    for f in files:
        try:
            print(f"\033[33m⏳\033[0m {f.name}  →  {args.to.upper()}", end="  ", flush=True)
            out = convert(f, args.to, args)
            size_kb = out.stat().st_size // 1024
            print(f"\033[32m✓\033[0m  {out.name}  ({size_kb} KB)")
        except SystemExit:
            errored += 1
            if not args.batch:
                raise
        except Exception as e:
            print(f"\033[31m✗ {e}\033[0m")
            errored += 1

    if args.batch:
        ok = len(files) - errored
        print(f"\n\033[36m{ok}/{len(files)} archivos convertidos\033[0m")
