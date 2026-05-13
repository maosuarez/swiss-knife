import sys
import argparse
from pathlib import Path
import subprocess
import shutil


def _require_binary(name):
    if not shutil.which(name):
        print(f"Instala {name}")
        sys.exit(1)


def do_something(input_path: Path, quality: int) -> Path:
    ext = input_path.suffix.lower()
    output = input_path.with_name(f"{input_path.stem}_compressed{ext}")

    if ext in [".jpg", ".jpeg", ".png"]:
        from PIL import Image
        img = Image.open(input_path)
        img.save(output, optimize=True, quality=quality)
        return output

    if ext in [".mp4", ".mov", ".mkv"]:
        _require_binary("ffmpeg")
        subprocess.run([
            "ffmpeg", "-i", str(input_path),
            "-vcodec", "libx265",
            "-crf", "28",
            str(output)
        ])
        return output

    raise Exception("Formato no soportado")


def run():
    parser = argparse.ArgumentParser(description="Comprimir media")
    parser.add_argument("input")
    parser.add_argument("--quality", type=int, default=85)
    args = parser.parse_args()

    out = do_something(Path(args.input), args.quality)
    print(out)
