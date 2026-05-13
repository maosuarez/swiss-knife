import sys
import argparse


def _require(package):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        print(f"pip install {package}")
        sys.exit(1)


def do_something(text, output=None):
    qrcode = _require("qrcode")

    qr = qrcode.make(text)

    if output:
        qr.save(output)
        return f"Saved: {output}"
    else:
        return str(qr)


def run():
    parser = argparse.ArgumentParser(description="Generar QR")
    parser.add_argument("text")
    parser.add_argument("-o", "--output")

    args = parser.parse_args()

    print(do_something(args.text, args.output))
