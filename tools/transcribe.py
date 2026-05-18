"""
transcribe — Audio a texto
═══════════════════════════════════════════════════════════════
Convierte archivos de audio/video a texto usando Whisper (default)
o Google Speech Recognition (legacy).

Formatos soportados:  OGG · MP3 · WAV · FLAC · M4A · MP4 · MKV · WEBM · OPUS · WMA · AAC
Idiomas:              auto-detección por default (Whisper), o pasar --lang es-ES
Motores:              whisper (default) · google (legacy)
Modelos Whisper:      tiny · base (default) · small · medium · large
Diarización:          --diarize  (requiere pyannote.audio y HF_TOKEN en entorno)

Ejemplos:
    knife transcribe audio.ogg
    knife transcribe entrevista.mp3 --lang es-ES --output resultado.txt
    knife transcribe reunion.mp4 --diarize --output acta.md
    knife transcribe largo.mp3 --model small
    knife transcribe audio.ogg --engine google --chunk-size 30
    knife transcribe video.mkv --model medium --output transcripcion.md
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import argparse
import tempfile
from datetime import date
from pathlib import Path


# ─── Dependencias opcionales ──────────────────────────────────────────────────

def _require(package: str, pip_name: str | None = None, extra_note: str | None = None):
    """Importa un módulo o termina con mensaje de error claro."""
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        if extra_note:
            print(f"  {extra_note}")
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
    ".mkv": "matroska",
    ".webm": "webm",
    ".opus": "ogg",
    ".wma": "asf",
}

CHUNK_SIZE_DEFAULT = 55  # segundos — margen seguro bajo el límite de 60s de Google Speech


# ─── Helpers de idioma ────────────────────────────────────────────────────────

def bcp47_to_iso639(lang: str | None) -> str | None:
    """
    Convierte un código BCP-47 (ej: 'es-ES', 'en-US') al código ISO 639-1
    que espera Whisper (ej: 'es', 'en'). Si ya es corto, lo retorna tal cual.
    Si lang es None retorna None (auto-detección de Whisper).
    """
    if lang is None:
        return None
    # Tomar solo la parte antes del guion
    return lang.split("-")[0].lower()


# ─── Motor Whisper ────────────────────────────────────────────────────────────

def _advertir_sin_gpu(model_name: str) -> None:
    """Muestra advertencia si el modelo es pesado y no hay GPU disponible."""
    if model_name not in ("medium", "large"):
        return
    try:
        import importlib
        torch = importlib.import_module("torch")
        if not torch.cuda.is_available():
            print(
                f"\033[33m⚠  Modelo '{model_name}' sin GPU detectada — "
                "la transcripción será lenta.\033[0m"
            )
    except ImportError:
        # torch no disponible; la advertencia no aplica sin él
        pass


def transcribe_whisper(
    input_path: Path,
    lang_iso: str | None,
    model_name: str,
    verbose: bool,
) -> list[dict]:
    """
    Transcribe con Whisper y retorna lista de segmentos:
    [{"start": float, "end": float, "text": str}, ...]
    """
    whisper = _require("whisper", "openai-whisper")
    _advertir_sin_gpu(model_name)

    if verbose:
        print(f"  Cargando modelo Whisper '{model_name}'...")

    modelo = whisper.load_model(model_name)

    opciones = {}
    if lang_iso:
        opciones["language"] = lang_iso

    if verbose:
        print(f"  Procesando audio...")

    resultado = modelo.transcribe(str(input_path), **opciones)
    segmentos = resultado.get("segments", [])

    return [
        {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
        for s in segmentos
    ]


# ─── Diarización con pyannote ─────────────────────────────────────────────────

def diarize_audio(input_path: Path) -> list[tuple[float, float, str]]:
    """
    Ejecuta diarización con pyannote.audio.
    Retorna lista de (start, end, speaker_label) donde speaker_label
    es 'Hablante 1', 'Hablante 2', etc.
    Requiere HF_TOKEN en variables de entorno.
    """
    # Importación tardía — pyannote solo se carga si se necesita
    try:
        import importlib
        pyannote_pipeline = importlib.import_module("pyannote.audio")
    except ImportError:
        print("\033[31m✗ Falta dependencia: 'pyannote.audio'\033[0m")
        print("  Instala con:  pip install pyannote.audio")
        print("  Además necesitas un token de HuggingFace en la variable HF_TOKEN.")
        sys.exit(1)

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("\033[31m✗ Variable de entorno HF_TOKEN no encontrada.\033[0m")
        print("  Genera un token en https://huggingface.co/settings/tokens")
        print("  y ejecútalo con:  set HF_TOKEN=<tu_token>")
        sys.exit(1)

    from pyannote.audio import Pipeline  # noqa: PLC0415

    print("  Cargando pipeline de diarización...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )

    print("  Ejecutando diarización...")
    diarizacion = pipeline(str(input_path))

    # Mapear IDs internos (SPEAKER_00, SPEAKER_01…) a nombres amigables
    id_a_nombre: dict[str, str] = {}
    contador = 1
    intervalos: list[tuple[float, float, str]] = []

    for turno, _, hablante_id in diarizacion.itertracks(yield_label=True):
        if hablante_id not in id_a_nombre:
            id_a_nombre[hablante_id] = f"Hablante {contador}"
            contador += 1
        nombre = id_a_nombre[hablante_id]
        intervalos.append((turno.start, turno.end, nombre))

    return intervalos


def asignar_hablantes(
    segmentos: list[dict],
    intervalos_diarizacion: list[tuple[float, float, str]],
) -> list[dict]:
    """
    Asigna a cada segmento de Whisper el hablante con mayor superposición
    en los intervalos de diarización.
    Agrega clave 'speaker' a cada segmento.
    """
    resultado = []
    for seg in segmentos:
        seg_start = seg["start"]
        seg_end = seg["end"]
        mejor_hablante = None
        mejor_superposicion = 0.0

        for (d_start, d_end, nombre) in intervalos_diarizacion:
            # Calcular superposición entre [seg_start, seg_end] y [d_start, d_end]
            overlap_start = max(seg_start, d_start)
            overlap_end = min(seg_end, d_end)
            superposicion = max(0.0, overlap_end - overlap_start)
            if superposicion > mejor_superposicion:
                mejor_superposicion = superposicion
                mejor_hablante = nombre

        resultado.append({**seg, "speaker": mejor_hablante})

    return resultado


# ─── Motor Google (legacy) ────────────────────────────────────────────────────

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
    Transcribe un archivo de audio completo con Google Speech Recognition,
    dividiéndolo en chunks para evitar el límite de ~60s gratuito.
    """
    sr = _require("speech_recognition", "SpeechRecognition")

    audio = load_audio(input_path)
    duration_s = len(audio) / 1000
    chunk_ms = chunk_seconds * 1000
    n_chunks = -(-int(len(audio)) // chunk_ms)  # división techo
    recognizer = sr.Recognizer()
    results = []

    if verbose or duration_s > chunk_seconds:
        print(f"  Duración: {duration_s:.0f}s  |  Chunks: {n_chunks} × {chunk_seconds}s")

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start : start + chunk_ms]

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            chunk.export(tmp_path, format="wav")

        try:
            with sr.AudioFile(str(tmp_path)) as source:
                audio_data = recognizer.record(source)
            text = transcribe_segment(recognizer, audio_data, lang)
            results.append(text)

            bar = "█" * (i + 1) + "░" * (n_chunks - i - 1)
            print(f"  [{bar}] {i+1}/{n_chunks}", end="\r", flush=True)
        finally:
            tmp_path.unlink(missing_ok=True)

    print()  # salto de línea tras la barra de progreso
    return " ".join(results)


# ─── Formateo de salida ───────────────────────────────────────────────────────

def _ts(segundos: float) -> str:
    """Convierte segundos a formato MM:SS."""
    minutos = int(segundos) // 60
    segs = int(segundos) % 60
    return f"{minutos:02d}:{segs:02d}"


def format_segments_console(segmentos: list[dict], con_diarizacion: bool) -> str:
    """
    Genera el texto para imprimir en consola desde segmentos de Whisper.
    Con diarización: '[MM:SS] Hablante X: texto'
    Sin diarización: '[MM:SS] texto'
    """
    lineas = []
    for seg in segmentos:
        marca = _ts(seg["start"])
        if con_diarizacion and seg.get("speaker"):
            lineas.append(f"[{marca}] {seg['speaker']}: {seg['text']}")
        else:
            lineas.append(f"[{marca}] {seg['text']}")
    return "\n".join(lineas)


def format_segments_md(
    segmentos: list[dict],
    nombre_archivo: str,
    lang_display: str,
    model_name: str,
    con_diarizacion: bool,
) -> str:
    """
    Genera contenido Markdown estructurado desde segmentos de Whisper.
    """
    fecha = date.today().isoformat()
    motor_str = f"Whisper ({model_name})"

    lineas = [
        f"# Transcripción: {nombre_archivo}",
        f"**Fecha:** {fecha}  ",
        f"**Idioma:** {lang_display}  ",
        f"**Motor:** {motor_str}",
        "",
        "---",
        "",
        "## Transcripción",
        "",
    ]

    for seg in segmentos:
        marca = _ts(seg["start"])
        if con_diarizacion and seg.get("speaker"):
            lineas.append(f"[{marca}] **{seg['speaker']}:** {seg['text']}")
        else:
            lineas.append(f"[{marca}] {seg['text']}")
        lineas.append("")  # línea en blanco entre segmentos

    return "\n".join(lineas)


# ─── Punto de entrada del CLI ─────────────────────────────────────────────────

def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife transcribe",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "audio",
        help="Archivo de audio/video a transcribir",
    )
    parser.add_argument(
        "--engine", "-e",
        choices=["whisper", "google"],
        default="whisper",
        help="Motor de transcripción: whisper (default) o google (legacy)",
    )
    parser.add_argument(
        "--model", "-m",
        choices=["tiny", "base", "small", "medium", "large"],
        default="base",
        metavar="MODEL",
        help="Modelo Whisper: tiny, base (default), small, medium, large",
    )
    parser.add_argument(
        "--lang", "-l",
        default=None,
        metavar="LANG",
        help=(
            "Idioma de reconocimiento. Con Whisper: auto-detección si se omite. "
            "Acepta BCP-47 (ej: es-ES, en-US) o ISO 639-1 (ej: es, en). "
            "Con Google: se pasa tal cual (ej: es-ES)."
        ),
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Activar diarización de hablantes (solo con --engine whisper). "
             "Requiere pyannote.audio y HF_TOKEN en entorno.",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Guardar transcripción en archivo. Usa .md para formato Markdown o .txt para texto plano.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE_DEFAULT,
        metavar="SEGUNDOS",
        help=f"Duración de cada chunk en segundos (solo con --engine google, default: {CHUNK_SIZE_DEFAULT}).",
    )
    parser.add_argument(
        "--keep-wav",
        action="store_true",
        help="[Deprecado] Flag ignorado silenciosamente para compatibilidad con scripts existentes.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar detalles del proceso",
    )

    args = parser.parse_args()

    # ── Validar archivo de entrada ────────────────────────────────────────────
    input_path = Path(args.audio)
    if not input_path.exists():
        print(f"\033[31m✗ Archivo no encontrado: {input_path}\033[0m")
        sys.exit(1)

    ext = input_path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        print(f"\033[31m✗ Formato no soportado: {ext}\033[0m")
        print(f"  Formatos válidos: {', '.join(SUPPORTED_FORMATS)}")
        sys.exit(1)

    # ── Validar combinaciones de flags ────────────────────────────────────────
    if args.diarize and args.engine == "google":
        print("\033[31m✗ --diarize solo está disponible con --engine whisper.\033[0m")
        sys.exit(1)

    # ── Ejecutar transcripción ────────────────────────────────────────────────
    if args.engine == "whisper":
        lang_iso = bcp47_to_iso639(args.lang)
        lang_display = lang_iso if lang_iso else "auto"

        print(
            f"\033[33m⏳ Transcribiendo:\033[0m {input_path.name}  "
            f"[whisper/{args.model}] [idioma: {lang_display}]"
        )

        segmentos = transcribe_whisper(
            input_path,
            lang_iso=lang_iso,
            model_name=args.model,
            verbose=args.verbose,
        )

        # Diarización opcional
        con_diarizacion = args.diarize
        if con_diarizacion:
            print("  Ejecutando diarización de hablantes...")
            intervalos = diarize_audio(input_path)
            segmentos = asignar_hablantes(segmentos, intervalos)

        # Imprimir en consola
        texto_consola = format_segments_console(segmentos, con_diarizacion)
        print(f"\n\033[32m✓ Transcripción:\033[0m\n")
        print(texto_consola)
        print()

        # Guardar en archivo si se pidió
        if args.output:
            out = Path(args.output)
            if out.suffix.lower() == ".md":
                contenido = format_segments_md(
                    segmentos,
                    nombre_archivo=input_path.name,
                    lang_display=lang_display,
                    model_name=args.model,
                    con_diarizacion=con_diarizacion,
                )
            else:
                # .txt u otra extensión — texto plano
                contenido = texto_consola

            out.write_text(contenido, encoding="utf-8")
            print(f"\033[36m💾 Guardado en: {out.resolve()}\033[0m\n")

    else:
        # ── Motor Google (legacy) ─────────────────────────────────────────────
        lang_google = args.lang if args.lang else "es-ES"

        print(f"\033[33m⏳ Transcribiendo:\033[0m {input_path.name}  [google] [{lang_google}]")

        result = transcribe_audio(
            input_path,
            lang=lang_google,
            chunk_seconds=args.chunk_size,
            verbose=args.verbose,
        )

        print(f"\n\033[32m✓ Transcripción:\033[0m\n")
        print(f"  {result}\n")

        if args.output:
            out = Path(args.output)
            out.write_text(result, encoding="utf-8")
            print(f"\033[36m💾 Guardado en: {out.resolve()}\033[0m\n")
