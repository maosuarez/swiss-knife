#!/usr/bin/env python3
"""Swiss Knife MCP Server — exposes knife tools to AI agents via Model Context Protocol."""

import sys
import base64
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path

# Make tool modules importable
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP
from mcp.types import ImageContent, TextContent

mcp = FastMCP("swiss-knife")


# ─── QR ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_qr(
    content: str,
    fg_color: str = "black",
    bg_color: str = "white",
    ecc: str = "M",
) -> list:
    """Generate a QR code and return it as an inline image in the chat.

    Args:
        content: Text, URL, or data to encode in the QR code.
        fg_color: Foreground color name or hex (default: black).
        bg_color: Background color name or hex (default: white).
        ecc: Error correction level — L, M, Q, or H (default: M).
    """
    import qrcode  # type: ignore

    ecc_map = {"L": qrcode.constants.ERROR_CORRECT_L,
               "M": qrcode.constants.ERROR_CORRECT_M,
               "Q": qrcode.constants.ERROR_CORRECT_Q,
               "H": qrcode.constants.ERROR_CORRECT_H}
    error_correct = ecc_map.get(ecc.upper(), qrcode.constants.ERROR_CORRECT_M)

    qr = qrcode.QRCode(error_correction=error_correct, box_size=10, border=4)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg_color, back_color=bg_color)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return [
        TextContent(type="text", text=f"QR code generated for: `{content}`\nECC: {ecc.upper()} | Colors: {fg_color}/{bg_color}"),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]


# ─── IMG-INFO ─────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_img_info(file_path: str) -> str:
    """Read EXIF and image metadata from an image file. Returns a markdown table.

    Args:
        file_path: Absolute path to the image file (JPG, PNG, WEBP, TIFF).
    """
    path = Path(file_path)
    if not path.exists():
        return f"Error: file not found — {file_path}"

    from PIL import Image
    from PIL.ExifTags import TAGS

    img = Image.open(path)
    lines = [
        f"| Field | Value |",
        f"|---|---|",
        f"| **Format** | {img.format} |",
        f"| **Mode** | {img.mode} |",
        f"| **Size** | {img.width} × {img.height} px |",
        f"| **File size** | {path.stat().st_size // 1024} KB |",
    ]

    exif_raw = img._getexif()  # type: ignore[attr-defined]
    if exif_raw:
        for tag_id, value in exif_raw.items():
            tag = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                continue
            if isinstance(value, tuple) and len(value) == 2:
                value = f"{value[0]}/{value[1]}"
            lines.append(f"| **{tag}** | {str(value)[:120]} |")
    else:
        lines.append("| **EXIF** | No EXIF data found |")

    return "\n".join(lines)


# ─── CRYPTO ───────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_crypto(text: str, option: str) -> str:
    """Encrypt, decrypt, encode, or decode text using classical ciphers and encodings.

    Args:
        text: The input text to process.
        option: Operation in format algorithm:mode[:params].
                Ciphers: caesar:enc:3 | caesar:dec:3 | caesar:brute
                         vigenere:enc:key | vigenere:dec:key
                         affine:enc:a:b | rail:enc:3 | columnar:enc:key
                Encoding: base64:enc | base64:dec
                          url:enc | url:dec
                          html:enc | html:dec
                          jwt:dec
    """
    from tools.encryption import do_something

    try:
        result = do_something(text, option)
        return f"```\n{result}\n```"
    except Exception as e:
        return f"Error: {e}"


# ─── PDF MERGE ────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_pdf_merge(files: list[str], output_path: str) -> str:
    """Merge multiple PDF files into one.

    Args:
        files: List of absolute paths to PDF files, in merge order.
        output_path: Absolute path for the output merged PDF.
    """
    missing = [f for f in files if not Path(f).exists()]
    if missing:
        return f"Error: files not found — {', '.join(missing)}"

    import PyPDF2  # type: ignore

    merger = PyPDF2.PdfMerger()
    for f in files:
        merger.append(f)
    merger.write(output_path)
    merger.close()

    out = Path(output_path)
    reader = PyPDF2.PdfReader(output_path)
    page_count = len(reader.pages)
    size_kb = out.stat().st_size // 1024

    return (
        f"**PDF merged successfully**\n\n"
        f"| | |\n|---|---|\n"
        f"| Output | `{output_path}` |\n"
        f"| Pages | {page_count} |\n"
        f"| Size | {size_kb} KB |\n"
        f"| Sources | {len(files)} files |"
    )


# ─── PDF SPLIT ────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_pdf_split(input_path: str, ranges: str, output_dir: str = "") -> str:
    """Split a PDF into separate files by page ranges.

    Args:
        input_path: Absolute path to the source PDF.
        ranges: Page ranges to extract, comma-separated (e.g. '1-3,5,7-10').
                Pages are 1-indexed.
        output_dir: Directory for output files. Defaults to same dir as input.
    """
    if not Path(input_path).exists():
        return f"Error: file not found — {input_path}"

    import PyPDF2  # type: ignore

    reader = PyPDF2.PdfReader(input_path)
    total = len(reader.pages)
    out_dir = Path(output_dir) if output_dir else Path(input_path).parent
    stem = Path(input_path).stem
    outputs = []

    def parse_range(r: str) -> list[int]:
        if "-" in r:
            a, b = r.split("-")
            return list(range(int(a) - 1, int(b)))
        return [int(r) - 1]

    for chunk in ranges.split(","):
        chunk = chunk.strip()
        pages = parse_range(chunk)
        writer = PyPDF2.PdfWriter()
        for p in pages:
            if 0 <= p < total:
                writer.add_page(reader.pages[p])
        out_path = out_dir / f"{stem}_p{chunk.replace('-', '_')}.pdf"
        with open(out_path, "wb") as f:
            writer.write(f)
        outputs.append(f"`{out_path.name}` ({len(pages)} pages)")

    return f"**Split complete**\n\n" + "\n".join(f"- {o}" for o in outputs)


# ─── VIDEO FRAME ──────────────────────────────────────────────────────────────

@mcp.tool()
def knife_clip_frame(file_path: str, timestamp: str) -> list:
    """Extract a single frame from a video at a given timestamp.

    Use this when you need to visually analyze a specific moment in a video.
    Returns the frame as an inline image — the video is never sent to the model.

    Args:
        file_path: Absolute path to the video file.
        timestamp: Time position as HH:MM:SS, MM:SS, or seconds (e.g. '01:23', '83').
    """
    if not Path(file_path).exists():
        return [TextContent(type="text", text=f"Error: file not found — {file_path}")]

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", file_path, "-ss", timestamp,
             "-frames:v", "1", "-q:v", "3", tmp_path],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        os.unlink(tmp_path)
        return [TextContent(type="text", text=f"Error extracting frame: {e.stderr.decode()}")]
    except FileNotFoundError:
        return [TextContent(type="text", text="Error: ffmpeg not found. Install with: conda install -c conda-forge ffmpeg")]

    with open(tmp_path, "rb") as f:
        img_bytes = f.read()
    os.unlink(tmp_path)

    b64 = base64.b64encode(img_bytes).decode()
    name = Path(file_path).name

    return [
        TextContent(type="text", text=f"Frame from **{name}** at `{timestamp}`"),
        ImageContent(type="image", data=b64, mimeType="image/jpeg"),
    ]


# ─── CLIP TRIM ────────────────────────────────────────────────────────────────

@mcp.tool()
def knife_clip_trim(file_path: str, start: str, end: str, output_path: str = "") -> str:
    """Trim a video or audio file by time range without re-encoding.

    Args:
        file_path: Absolute path to the video or audio file.
        start: Start time as HH:MM:SS, MM:SS, or seconds.
        end: End time as HH:MM:SS, MM:SS, or seconds.
        output_path: Output file path. Defaults to input_clip.ext in same directory.
    """
    if not Path(file_path).exists():
        return f"Error: file not found — {file_path}"

    src = Path(file_path)
    out = Path(output_path) if output_path else src.with_stem(src.stem + "_clip")

    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error",
             "-i", file_path, "-ss", start, "-to", end,
             "-c", "copy", str(out)],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.decode()}"
    except FileNotFoundError:
        return "Error: ffmpeg not found. Install with: conda install -c conda-forge ffmpeg"

    size_kb = out.stat().st_size // 1024
    return (
        f"**Clip saved**\n\n"
        f"| | |\n|---|---|\n"
        f"| Output | `{out}` |\n"
        f"| Range | `{start}` → `{end}` |\n"
        f"| Size | {size_kb} KB |"
    )


# ─── TRANSCRIBE ───────────────────────────────────────────────────────────────

@mcp.tool()
def knife_transcribe(file_path: str) -> str:
    """Transcribe audio or video to text. Returns transcript as markdown.

    The model receives the text transcript — never the raw audio.
    For long files, only the first segment is returned; use the CLI for full transcription.

    Args:
        file_path: Absolute path to audio/video file (MP3, WAV, MP4, M4A, etc.).
    """
    if not Path(file_path).exists():
        return f"Error: file not found — {file_path}"

    try:
        import speech_recognition as sr  # type: ignore
        from pydub import AudioSegment  # type: ignore
    except ImportError as e:
        return f"Error: missing dependency — {e}. Run: pip install SpeechRecognition pydub"

    path = Path(file_path)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name

    try:
        audio = AudioSegment.from_file(str(path))
        # Only transcribe first 60s via MCP to avoid timeouts
        chunk = audio[:60_000]
        chunk.export(wav_path, format="wav")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    except Exception as e:
        return (
            f"Transcription error: {e}\n\n"
            f"For full transcription run:\n```\nknife transcribe \"{file_path}\"\n```"
        )
    finally:
        if os.path.exists(wav_path):
            os.unlink(wav_path)

    return (
        f"**Transcript** (first 60s of `{path.name}`):\n\n"
        f"> {text}\n\n"
        f"*For full transcription with speaker separation, run:*\n"
        f"```\nknife transcribe \"{file_path}\"\n```"
    )


if __name__ == "__main__":
    mcp.run()
