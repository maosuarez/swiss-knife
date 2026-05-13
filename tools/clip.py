import sys
import argparse
from pathlib import Path
import subprocess
import shutil


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _require_binary(name):
    if not shutil.which(name):
        print(f"\033[31m✗ Falta binario: {name}\033[0m")
        print(f"  Instala con: sudo apt install {name}")
        sys.exit(1)


def _run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode())
        sys.exit(1)


def parse_time(t: str) -> str:
    """
    Acepta:
    - 90
    - 1:30
    - 00:01:30
    Devuelve formato HH:MM:SS
    """
    parts = t.split(":")
    if len(parts) == 1:
        return f"00:00:{int(parts[0]):02d}"
    elif len(parts) == 2:
        return f"00:{int(parts[0]):02d}:{int(parts[1]):02d}"
    elif len(parts) == 3:
        return f"{int(parts[0]):02d}:{int(parts[1]):02d}:{int(parts[2]):02d}"
    else:
        raise ValueError("Formato de tiempo inválido")


# ─── Lógica principal ─────────────────────────────────────────────────────────
def do_something(input_path: Path, start: str, end: str, args) -> Path:
    _require_binary("ffmpeg")

    start_t = parse_time(start)
    end_t = parse_time(end)

    output = input_path.with_name(
        f"{input_path.stem}_clip{input_path.suffix}"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-ss", start_t,
        "-to", end_t,
    ]

    # ─── Sin pérdida (stream copy)
    if not args.reencode:
        cmd += ["-c", "copy"]
    else:
        # fallback cuando copy falla (keyframes)
        cmd += ["-c:v", "libx264", "-c:a", "aac"]

    cmd.append(str(output))

    _run(cmd)
    return output


# ─── CLI ─────────────────────────────────────────────────────────────────────
def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife clip",
        description="""
Recorta audio o video sin pérdida de calidad.

Usa ffmpeg con stream copy (-c copy) para evitar recodificación.

Formatos soportados:
- Video: mp4, mkv, avi, mov
- Audio: mp3, wav, m4a

Formato de tiempo:
- segundos:      90
- minutos:       1:30
- completo:      00:01:30

Ejemplos:
  knife clip video.mp4 --start 1:30 --end 2:45
  knife clip audio.mp3 --start 30 --end 90
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", help="Archivo de entrada")

    parser.add_argument("--start", required=True,
                        help="Tiempo inicial (ej: 1:30)")

    parser.add_argument("--end", required=True,
                        help="Tiempo final (ej: 2:45)")

    parser.add_argument("--reencode",
                        action="store_true",
                        help="Forzar recodificación (si falla sin pérdida)")

    parser.add_argument("--verbose", "-v",
                        action="store_true")

    args = parser.parse_args()

    input_path = Path(args.input)

    if not input_path.exists():
        print(f"\033[31m✗ No existe: {input_path}\033[0m")
        sys.exit(1)

    print(f"\033[33m⏳ Recortando:\033[0m {input_path.name}")

    try:
        output = do_something(input_path, args.start, args.end, args)
        print(f"\033[32m✓ Clip generado:\033[0m {output}")
    except Exception as e:
        print(f"\033[31m✗ Error:\033[0m {str(e)}")
        sys.exit(1)
