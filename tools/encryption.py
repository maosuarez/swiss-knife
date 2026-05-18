"""
🔐 crypto — Cifrado, análisis y codificación de textos
═══════════════════════════════════════════════════════════════
Cifra, descifra, ataca y codifica textos.

Cifrados:     caesar · vigenere · base64 · affine · rail · columnar
Codificación: url · html · jwt

Entrada:      archivo de texto o cadena directa
Salida:       texto en pantalla o --output FILE

Ejemplos:
    knife crypto mensaje.txt --option caesar:brute
    knife crypto "HELLO" --option caesar:enc:3
    knife crypto cifrado.txt --option vigenere:dec:clave
    knife crypto datos.txt --option base64:enc
    knife crypto "hello world" --option url:enc
    knife crypto "eyJhbGciOiJ..." --option jwt:dec
═══════════════════════════════════════════════════════════════
"""

import sys
import argparse
from pathlib import Path
import base64
import string
import urllib.parse
import html as html_module
from itertools import permutations


# ─── Helper opcional ──────────────────────────────────────────────────────────
def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Falta dependencia: '{package}'\033[0m")
        print(f"  Instala con:  pip install {pip_name}")
        sys.exit(1)


# ─── CIFRADOS ────────────────────────────────────────────────────────────────

# --- César ---
def caesar(text, shift, decrypt=False):
    if decrypt:
        shift = -shift
    result = ""
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result += chr((ord(c) - base + shift) % 26 + base)
        else:
            result += c
    return result


def caesar_bruteforce(text):
    return "\n".join([f"{i}: {caesar(text, i, True)}" for i in range(26)])


# --- Vigenère ---
def vigenere(text, key, decrypt=False):
    key = key.lower()
    result = ""
    j = 0
    for c in text:
        if c.isalpha():
            shift = ord(key[j % len(key)]) - ord('a')
            if decrypt:
                shift = -shift
            base = ord('A') if c.isupper() else ord('a')
            result += chr((ord(c) - base + shift) % 26 + base)
            j += 1
        else:
            result += c
    return result


def vigenere_dict_attack(text, dict_path):
    words = Path(dict_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    results = []
    for word in words:
        if word.isalpha():
            dec = vigenere(text, word, decrypt=True)
            if " " in dec:  # heurística simple
                results.append(f"{word}: {dec}")
    return "\n".join(results[:50])


# --- Base64 ---
def b64(text, decrypt=False):
    if decrypt:
        return base64.b64decode(text.encode()).decode(errors="ignore")
    return base64.b64encode(text.encode()).decode()


# --- Afín ---
def modinv(a, m):
    for x in range(1, m):
        if (a * x) % m == 1:
            return x
    return None


def affine(text, a, b, decrypt=False):
    result = ""
    if decrypt:
        inv = modinv(a, 26)
        if inv is None:
            return "No inverso modular"
    for c in text:
        if c.isalpha():
            x = ord(c.lower()) - ord('a')
            if decrypt:
                val = (inv * (x - b)) % 26
            else:
                val = (a * x + b) % 26
            result += chr(val + ord('a'))
        else:
            result += c
    return result


# --- Rail Fence ---
def rail_fence(text, rails, decrypt=False):
    if decrypt:
        fence = [[] for _ in range(rails)]
        pattern = list(range(rails)) + list(range(rails - 2, 0, -1))
        pattern_len = len(pattern)

        idx = 0
        for i in range(len(text)):
            fence[pattern[i % pattern_len]].append(None)

        for r in range(rails):
            for i in range(len(fence[r])):
                fence[r][i] = text[idx]
                idx += 1

        result = ""
        pointers = [0] * rails
        for i in range(len(text)):
            r = pattern[i % pattern_len]
            result += fence[r][pointers[r]]
            pointers[r] += 1
        return result

    rail = [''] * rails
    pattern = list(range(rails)) + list(range(rails - 2, 0, -1))
    for i, c in enumerate(text):
        rail[pattern[i % len(pattern)]] += c
    return ''.join(rail)


# --- Columnar ---
def columnar(text, key, decrypt=False):
    key_order = sorted(range(len(key)), key=lambda k: key[k])

    if decrypt:
        n_cols = len(key)
        n_rows = len(text) // n_cols
        grid = [''] * n_cols
        idx = 0
        for i in key_order:
            grid[i] = text[idx:idx+n_rows]
            idx += n_rows

        result = ""
        for r in range(n_rows):
            for c in range(n_cols):
                result += grid[c][r]
        return result

    n_cols = len(key)
    n_rows = -(-len(text) // n_cols)
    padded = text.ljust(n_rows * n_cols, 'X')

    grid = [padded[i:i+n_cols] for i in range(0, len(padded), n_cols)]

    result = ""
    for i in key_order:
        for row in grid:
            result += row[i]
    return result


# ─── Lógica principal ─────────────────────────────────────────────────────────

def do_something(input_data, option: str) -> str:

    if isinstance(input_data, Path):
        text = input_data.read_text(encoding="utf-8", errors="ignore")
    else:
        text = input_data

    algo, mode, *params = option.split(":")

    if algo == "caesar":
        if mode == "enc":
            return caesar(text, int(params[0]))
        elif mode == "dec":
            return caesar(text, int(params[0]), True)
        elif mode == "brute":
            return caesar_bruteforce(text)

    elif algo == "vigenere":
        if mode == "enc":
            return vigenere(text, params[0])
        elif mode == "dec":
            return vigenere(text, params[0], True)
        elif mode == "dict":
            return vigenere_dict_attack(text, params[0])

    elif algo == "base64":
        return b64(text, decrypt=(mode == "dec"))

    elif algo == "affine":
        a, b = int(params[0]), int(params[1])
        return affine(text, a, b, decrypt=(mode == "dec"))

    elif algo == "rail":
        rails = int(params[0])
        return rail_fence(text, rails, decrypt=(mode == "dec"))

    elif algo == "columnar":
        key = params[0]
        return columnar(text, key, decrypt=(mode == "dec"))

    elif algo == "url":
        if mode == "enc":
            return urllib.parse.quote(text, safe="")
        elif mode == "dec":
            return urllib.parse.unquote(text)

    elif algo == "html":
        if mode == "enc":
            return html_module.escape(text)
        elif mode == "dec":
            return html_module.unescape(text)

    elif algo == "jwt":
        jwt = _require("jwt", "PyJWT")
        try:
            header = jwt.get_unverified_header(text)
            payload = jwt.decode(text, options={"verify_signature": False})
            return (
                f"Header:\n{__import__('json').dumps(header, indent=2)}\n\n"
                f"Payload:\n{__import__('json').dumps(payload, indent=2, default=str)}"
            )
        except Exception as e:
            return f"JWT inválido: {e}"

    return "Algoritmo o modo no soportado"


# ─── CLI ─────────────────────────────────────────────────────────────────────

def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife crypto",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("input", help="Archivo o ruta de entrada")

    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Archivo de salida (opcional)",
    )

    parser.add_argument(
        "--option",
        default="caesar:brute",
        help="""Formato: algoritmo:modo:parametros

Algoritmos soportados:

  caesar:
    enc:<shift>        → cifrar
    dec:<shift>        → descifrar
    brute              → fuerza bruta

  vigenere:
    enc:<key>
    dec:<key>
    dict:<diccionario.txt>

  base64:
    enc
    dec

  affine:
    enc:<a>:<b>
    dec:<a>:<b>

  rail:
    enc:<rails>
    dec:<rails>

  columnar:
    enc:<key>
    dec:<key>

  url:
    enc              → percent-encoding (RFC 3986)
    dec              → decodificar URL

  html:
    enc              → escapar entidades HTML (&amp; &lt; &gt;)
    dec              → desescapar entidades HTML

  jwt:
    dec              → decodificar JWT sin verificar firma (inspección)

Ejemplos:
  --option caesar:enc:3
  --option caesar:brute
  --option vigenere:dec:clave
  --option vigenere:dict:rockyou.txt
  --option base64:dec
  --option url:enc
  --option html:enc
  --option jwt:dec
"""
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada del proceso",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.exists():
        text_source = input_path
    else:
        text_source = args.input  # texto directo

    print(f"\033[33m⏳ Procesando:\033[0m {input_path.name}")

    result = do_something(text_source, args.option)

    print(f"\033[32m✓ Resultado:\033[0m {result}")

    if args.output:
        out = Path(args.output)
        out.write_text(result, encoding="utf-8")
        print(f"\033[36m💾 Guardado en: {out.resolve()}\033[0m")
