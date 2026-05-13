See context.md for full project context.

## Contexto de migración Windows

La suite se ha migrado de **WSL/Ubuntu a Windows 11 nativo**. Los cambios clave que afectan las tareas:

- **Target**: Windows Terminal / PowerShell, no WSL. Python está en conda env `tools-env` (Python 3.11.15).
- **Punto de entrada CLI**: `pyproject.toml` con `[project.scripts] knife = "main:main"`. Se instala con `pip install -e .` en el env conda.
- **Binarios de sistema**: ffmpeg, pandoc viven en el env conda (`tools-env`), instalados vía `conda install -c conda-forge` — no son binarios globales.
- **Visual output**: Rich (`console.print()` con estilos) es la nueva norma. Migración de ANSI escape codes sucede tool-by-tool. Estilos: `yellow` = progreso, `green` = éxito, `red` = error, `cyan` = info.
- **Mensajes `_require()`**: deben referenciar `conda install -c conda-forge` o `pip install`, no `sudo apt install`.
- **Conversión de docs**: `docx2pdf` usa COM de Word. `.pptx`/`.xlsx` requieren LibreOffice o fallback explícito.

## Rol del agente

Este es un proyecto de herramientas CLI. El agente asiste en la extensión, refactorización y mantenimiento de la suite. No ejecuta comandos en el sistema del usuario.

## Antes de cualquier tarea

1. Leer `context.md` para entender arquitectura y convenciones
2. Identificar si la tarea es: nueva herramienta, mejora de existente, refactor, o fix
3. Confirmar alcance antes de generar código

## Agregar una herramienta nueva

Secuencia obligatoria:

1. Usar `tools/_template.py` como base — no inventar estructura propia
2. Implementar `run()` + lógica interna separada en función(es) nombradas
3. Seguir patrón `_require()` para dependencias opcionales
4. Registrar en `TOOLS` de `main.py`
5. Agregar dependencias a `requirements.txt` si aplica

No generar código hasta que el usuario confirme la firma del CLI (args, flags, output esperado).

## Mejorar herramientas existentes

Las herramientas "ligeras" (`compress`, `merge_pdf`, `fetch`, `find_dup`, `img_info`, `qr`) están en estado mínimo funcional. Son candidatas a mejora, pero **no refactorizar sin pedido explícito**.

Al mejorar una herramienta:
- Mantener compatibilidad de CLI hacia atrás
- No cambiar el nombre del archivo ni de la función `run()`
- Preservar el estilo de colores y feedback visual existente

## Control de alcance

- No modificar más de un archivo por tarea salvo que sea necesario estructuralmente
- No agregar dependencias de sistema sin mencionarlo explícitamente
- No cambiar el patrón de registro en `main.py` — es intencional
- No agregar logging, tests ni CI sin que se pida

## Qué NO hacer

- No crear módulos de utilidades compartidas sin discutirlo primero
- No reemplazar `argparse` por otra librería de CLI
- No asumir que el usuario quiere implementación si solo preguntó por diseño
- No generar documentación `.md` adicional salvo que se pida explícitamente
- No modificar `setup.sh` a menos que el cambio afecte la instalación
