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


def do_something(files, output):
    PyPDF2 = _require("PyPDF2")
    merger = PyPDF2.PdfMerger()

    for f in files:
        merger.append(str(f))

    merger.write(output)
    merger.close()


def run():
    parser = argparse.ArgumentParser(description="Unir PDFs")
    parser.add_argument("files", nargs="+")
    parser.add_argument("-o", "--output", default="merged.pdf")

    args = parser.parse_args()

    do_something([Path(f) for f in args.files], args.output)
    print(args.output)
