#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  Swiss Knife — Setup
#  Configura el entorno, instala dependencias y registra el
#  comando `knife` globalmente en tu shell.
# ═══════════════════════════════════════════════════════════════

set -e

KNIFE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$KNIFE_DIR/.venv"
PROFILE_FILE="$HOME/.bashrc"

# Detectar zsh
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "$(which zsh)" ]; then
    PROFILE_FILE="$HOME/.zshrc"
fi

echo ""
echo "\033[33m╔══════════════════════════════════════════════════╗"
echo "║       🔪  Swiss Knife — Setup                    ║"
echo "╚══════════════════════════════════════════════════╝\033[0m"
echo ""

# 1. Dependencias de sistema
echo "\033[36m[1/4] Verificando dependencias del sistema...\033[0m"

# ── ffmpeg ────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "  ⚠ ffmpeg no encontrado. Instalando..."
    sudo apt update -qq && sudo apt install -y ffmpeg
else
    echo "  ✓ ffmpeg OK"
fi

# ── LibreOffice ───────────────────────────────────────────
if ! command -v libreoffice &>/dev/null; then
    echo "  ⚠ LibreOffice no encontrado. Instalando..."
    sudo apt update -qq && sudo apt install -y libreoffice
else
    echo "  ✓ LibreOffice OK"
fi

# ── Pandoc ────────────────────────────────────────────────
if ! command -v pandoc &>/dev/null; then
    echo "  ⚠ Pandoc no encontrado. Instalando..."
    sudo apt update -qq && sudo apt install -y pandoc
else
    echo "  ✓ Pandoc OK"
fi

# 2. Crear .venv
echo ""
echo "\033[36m[2/4] Configurando entorno virtual...\033[0m"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  ✓ .venv creado en $VENV_DIR"
else
    echo "  ✓ .venv ya existe"
fi

# 3. Instalar dependencias Python
echo ""
echo "\033[36m[3/4] Instalando dependencias Python...\033[0m"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$KNIFE_DIR/requirements.txt"
echo "  ✓ Dependencias instaladas"

# 4. Registrar alias global
echo ""
echo "\033[36m[4/4] Registrando comando 'knife' en $PROFILE_FILE...\033[0m"

ALIAS_LINE="alias knife='$VENV_DIR/bin/python $KNIFE_DIR/main.py'"
MARKER="# swiss-knife-alias"

if grep -q "$MARKER" "$PROFILE_FILE" 2>/dev/null; then
    # Reemplazar alias existente
    sed -i "/$MARKER/d" "$PROFILE_FILE"
    echo "  ↺ Alias actualizado"
fi

echo "" >> "$PROFILE_FILE"
echo "$MARKER" >> "$PROFILE_FILE"
echo "$ALIAS_LINE" >> "$PROFILE_FILE"
echo "  ✓ Alias registrado"

echo ""
echo "\033[32m══════════════════════════════════════════════════"
echo "  ✅  Instalación completada."
echo ""
echo "  Ejecuta:  source $PROFILE_FILE"
echo "  Luego:    knife --list"
echo "══════════════════════════════════════════════════\033[0m"
echo ""
