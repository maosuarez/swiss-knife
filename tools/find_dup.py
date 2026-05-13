import sys
import argparse
from pathlib import Path
import hashlib


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def do_something(input_path: Path) -> str:
    hashes = {}
    duplicates = []

    for file in input_path.rglob("*"):
        if file.is_file():
            h = file_hash(file)
            if h in hashes:
                duplicates.append((file, hashes[h]))
            else:
                hashes[h] = file

    if not duplicates:
        return "No duplicates found"

    return "\n".join([f"{a} == {b}" for a, b in duplicates])


def run():
    parser = argparse.ArgumentParser(description="Detecta duplicados por hash")
    parser.add_argument("input")
    args = parser.parse_args()

    path = Path(args.input)
    print(do_something(path))
