# Swiss Knife CLI

## Descripción

CLI modular tipo "navaja suiza" para Windows nativo. Centraliza herramientas de línea de comandos para tareas frecuentes de procesamiento de archivos, multimedia, criptografía y utilidades de sistema. Se invoca globalmente con el comando `knife <herramienta> [opciones]` desde PowerShell o Windows Terminal.

## Stack

- **Python 3.11.15** — lenguaje principal, instalado en conda env `tools-env`
- **ffmpeg** — conversión y recorte de audio/video (instalado vía `conda install -c conda-forge`)
- **Pandoc** — conversión entre formatos de markup (instalado vía `conda install -c conda-forge`)
- **docx2pdf** — conversión de `.docx` a PDF vía COM de Word
- **LibreOffice** — conversión de `.pptx`/`.xlsx` (opcional, fallback explícito si no está disponible)
- **Pillow** — procesamiento de imágenes
- **rembg / U2Net** — eliminación de fondos con IA local
- **SpeechRecognition + pydub** — transcripción de audio vía Google Speech
- **pdf2docx, PyPDF2** — manipulación de PDFs
- **requests + beautifulsoup4** — scraping de texto limpio
- **qrcode** — generación de QR
- **rich>=13.0** — output visual con colores y estilos
- **pywin32>=306** — acceso a COM de Windows para docx2pdf

## Arquitectura

```
swiss-knife/
├── main.py              # Dispatcher central — registra y despacha herramientas
├── pyproject.toml       # Definición de proyecto y punto de entrada CLI (knife)
├── setup.ps1            # Instalador Windows: conda env, Python, alias (PowerShell)
├── setup.sh             # [Congelado] Instalador WSL/Linux histórico (no mantenido)
├── requirements.txt     # Dependencias Python (heredado; pyproject.toml es primario)
└── tools/
    ├── _template.py     # Plantilla para nuevas herramientas
    ├── transcribe.py    # Audio → texto (Google Speech, chunked)
    ├── rembg_tool.py    # Eliminación de fondo (U2Net, local)
    ├── encryption.py    # Cifrado clásico (César, Vigenère, Afín, Rail Fence, Columnar, Base64)
    ├── convert.py       # Conversor multipropósito (audio, video, docs, datos, markup)
    ├── clip.py          # Recorte de audio/video sin pérdida (ffmpeg stream copy)
    ├── compress.py      # Compresión de imágenes (Pillow) y video (libx265)
    ├── merge_pdf.py     # Unión de PDFs (PyPDF2)
    ├── fetch.py         # Descarga de URL como texto limpio (BS4)
    ├── find_dup.py      # Detección de duplicados por hash SHA-256
    ├── img_info.py      # Extracción de metadata EXIF (Pillow)
    └── qr.py            # Generación de códigos QR
```

**Punto de entrada CLI:** `pyproject.toml` define `[project.scripts] knife = "main:main"`. Se instala con `pip install -e .` en el conda env `tools-env`. El ejecutable `knife.exe` se coloca en `tools-env\Scripts\` y está disponible globalmente cuando el env está activo. Opcionalmente, agregar `C:\Users\maosu\miniconda3\envs\tools-env\Scripts` al PATH del usuario para usar `knife` sin activar el env.

**Patrón de extensión:** cada herramienta expone exactamente una función `run()` sin argumentos. Lee sus propios args desde `sys.argv` con `argparse`. El dispatcher en `main.py` reemplaza `sys.argv[0]` antes de delegar.

**Registro de herramientas:** dict `TOOLS` en `main.py` → `"nombre": ("tools.modulo", "descripción")`. Añadir una herramienta nueva requiere: crear `tools/<nombre>.py`, agregar entrada en `TOOLS`, y declarar dependencias en `pyproject.toml` (o `requirements.txt` si aplica).

## Convenciones

- Idioma del código y comentarios: **español**
- Output visual: Rich `console.print()` con estilos (`yellow` = progreso, `green` = éxito, `red` = error, `cyan` = info). Cada herramienta importa localmente: `from rich.console import Console; console = Console()`. Migración de ANSI escape codes a rich sucede tool-by-tool conforme se usan las herramientas.
- Imports de dependencias opcionales: patrón `_require(package, pip_name)` dentro de cada módulo — falla con mensaje accionable referenciando `conda install -c conda-forge` o `pip install`, no con traceback
- Dependencias de sistema (ffmpeg, pandoc): viven en el conda env `tools-env`, instaladas vía `conda install -c conda-forge` — no son binarios globales de Windows
- Outputs de archivos generados: mismo directorio del input, con sufijo descriptivo (ej: `_clip`, `_compressed`, `_nobg`)
- Formato de tiempo en `clip.py`: acepta segundos enteros, `MM:SS` o `HH:MM:SS`
- Herramientas "ligeras" (`fetch`, `find_dup`, `img_info`, `qr`, `merge_pdf`, `compress`) están en estado funcional mínimo — pueden mejorarse progresivamente

## Restricciones técnicas

- El entorno de ejecución es **Windows 11 nativo** con **conda env `tools-env` (Python 3.11.15)**; no asumir WSL ni Linux
- `ffmpeg` y `pandoc` viven en el conda env `tools-env`, no en binarios globales de Windows — se invocan desde `tools-env\Scripts\` (disponible en PATH cuando el env está activo)
- `docx2pdf` usa COM de Word (requiere MS Word instalado). Si no está disponible, `convert.py` falla con mensaje claro ofreciendo LibreOffice como fallback
- `.pptx` y `.xlsx` aún requieren LibreOffice; `convert.py` los maneja con LibreOffice o falla con mensaje `_require()` explícito
- Las herramientas no deben tener estado compartido entre sí
- No crear CLIs anidados ni subcomandos con subparsers; cada tool es autónoma
- `transcribe.py` usa Google Speech gratuito — requiere internet y tiene límite de ~60s por chunk; por eso el chunking automático
- `rembg` descarga el modelo U2Net en el primer uso (~170 MB)
- No modificar `main.py` para lógica de negocio; solo para registro en `TOOLS`

## Contexto de negocio

Herramienta personal de productividad para uso diario en Windows 11 nativo con conda. Usuario único con perfil técnico avanzado. Los casos de uso principales son: transcribir notas de voz, convertir formatos de archivo, recortar clips de video/audio, eliminar fondos de imágenes, y procesar datos estructurados desde PowerShell/Windows Terminal. El diseño prioriza CLI minimalista, feedback visual claro y extensibilidad rápida.
