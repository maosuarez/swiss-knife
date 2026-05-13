import sys
import argparse
from pathlib import Path


def _require(package, pip_name=None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        print(f"pip install {pip_name or package}")
        sys.exit(1)


def do_something(input_path: Path) -> str:
    PIL = _require("PIL", "pillow")
    img = PIL.Image.open(input_path)

    exif = img._getexif()
    if not exif:
        return "No EXIF data"

    return "\n".join([f"{k}: {v}" for k, v in exif.items()])


def run():
    parser = argparse.ArgumentParser(description="Metadata EXIF")
    parser.add_argument("input")
    args = parser.parse_args()

    print(do_something(Path(args.input)))
