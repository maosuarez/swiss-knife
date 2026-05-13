"""
🎙️ transcribe — Audio a texto
═══════════════════════════════════════════════════════════════
Convierte archivos de audio a texto usando Google Speech Recognition.
Soporta audios largos dividiéndolos automáticamente en chunks.

Formatos soportados:  OGG · MP3 · WAV · FLAC · M4A · MP4
Idiomas:              es-ES (default), en-US, fr-FR, pt-BR, etc.

Ejemplos:
    knife transcribe audio.ogg
    knife transcribe entrevista.mp3 --lang es-ES --output resultado.txt
    knife transcribe largo.mp3 --chunk-size 30
    knife transcribe audio.ogg --keep-wav
═══════════════════════════════════════════════════════════════
"""

import sys
import argparse
import tempfile
from pathlib import Path

# ─── Dependencias opcionales ──────────────────────────────────────────────────

def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        sys.exit(1)


# ─── Formatos soportados ──────────────────────────────────────────────────────

SUPPORTED_FORMATS = {
    ".ogg": "ogg",
    ".mp3": "mp3",
    ".wav": "wav",
    ".flac": "flac",
    ".m4a": "mp4",
    ".mp4": "mp4",
    ".aac": "aac",
}

CHUNK_SIZE_DEFAULT = 55  # segundos — margen seguro bajo el límite de 60s de Google


def load_audio(input_path: Path):
    """Carga el audio como AudioSegment independiente del formato."""
    pydub = _require("pydub", "pydub")
    ext = input_path.suffix.lower()
    fmt = SUPPORTED_FORMATS.get(ext)
    if not fmt:
        print(f"\033[31m✗ Formato no soportado: {ext}\033[0m")
        print(f"  Formatos válidos: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)
    return pydub.AudioSegment.from_file(str(input_path), format=fmt)


def transcribe_segment(recognizer, audio_data, lang: str) -> str:
    """Intenta transcribir un segmento de audio. Retorna texto o placeholder."""
    sr = _require("speech_recognition", "SpeechRecognition")
    try:
        return recognizer.recognize_google(audio_data, language=lang)
    except sr.UnknownValueError:
        return "[segmento no inteligible]"
    except sr.RequestError as e:
        print(f"\n\033[31m✗ Error de conexión con Google Speech: {e}\033[0m")
        print("  Verifica tu conexión a internet e intenta de nuevo.")
        sys.exit(1)


def transcribe_audio(input_path: Path, lang: str, chunk_seconds: int, verbose: bool) -> str:
    """
    Transcribe un archivo de audio completo dividiéndolo en chunks
    para evitar el límite de ~60s de Google Speech Recognition gratuito.
    """
    sr = _require("speech_recognition", "SpeechRecognition")

    audio = load_audio(input_path)
    duration_s = len(audio) / 1000
    chunk_ms = chunk_seconds * 1000

    n_chunks = -(-int(len(audio)) // chunk_ms)  # ceil division
    recognizer = sr.Recognizer()
    results = []

    if verbose or duration_s > chunk_seconds:
        print(f"  Duración: {duration_s:.0f}s  |  Chunks: {n_chunks} × {chunk_seconds}s")

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]

        # Exportar chunk a WAV temporal en memoria
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            chunk.export(tmp_path, format="wav")

        try:
            with sr.AudioFile(str(tmp_path)) as source:
                audio_data = recognizer.record(source)
            text = transcribe_segment(recognizer, audio_data, lang)
            results.append(text)

            # Progreso inline
            bar = "█" * (i + 1) + "░" * (n_chunks - i - 1)
            print(f"  [{bar}] {i+1}/{n_chunks}", end="\r", flush=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    print()  # salto de línea tras la barra de progreso
    return " ".join(results)


# ─── Punto de entrada del CLI ─────────────────────────────────────────────────

def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife transcribe",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "audio",
        help="Archivo de audio/video a transcribir (OGG, MP3, WAV, FLAC, M4A, MP4)",
    )
    parser.add_argument(
        "--lang", "-l",
        default="es-ES",
        metavar="LANG",
        help="Idioma de reconocimiento (default: es-ES). Ej: en-US, fr-FR, pt-BR",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Guardar transcripción en un archivo de texto",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE_DEFAULT,
        metavar="SEGUNDOS",
        help=f"Duración de cada chunk en segundos (default: {CHUNK_SIZE_DEFAULT}). "
             "Reduce si sigues teniendo errores de conexión.",
    )
    parser.add_argument(
        "--keep-wav",
        action="store_true",
        help="[Deprecado] Los WAV temporales ahora se manejan internamente.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalles del proceso",
    )

    args = parser.parse_args()

    input_path = Path(args.audio)
    if not input_path.exists():
        print(f"\033[31m✗ Archivo no encontrado: {input_path}\033[0m")
        sys.exit(1)

    print(f"\033[33m⏳ Transcribiendo:\033[0m {input_path.name}  [{args.lang}]")

    result = transcribe_audio(
        input_path,
        lang=args.lang,
        chunk_seconds=args.chunk_size,
        verbose=args.verbose,
    )

    print(f"\n\033[32m✓ Transcripción:\033[0m\n")
    print(f"  {result}\n")

    if args.output:
        out = Path(args.output)
        out.write_text(result, encoding="utf-8")
        print(f"\033[36m💾 Guardado en: {out.resolve()}\033[0m\n")
