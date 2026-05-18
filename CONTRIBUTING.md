# Contributing to Swiss Knife

Thank you for your interest in contributing to Swiss Knife! This document outlines how to set up your development environment, add new tools, and submit pull requests.

## Our Philosophy

Swiss Knife is built on simplicity:

- **One CLI, Many Tools** — Each tool does one thing well and independently. No shared state, no cross-tool coupling.
- **Local-First** — All processing happens on the user's machine. No cloud, no API calls, no rate limits.
- **Windows Native** — Swiss Knife is optimized for Windows PowerShell and Windows Terminal.
- **Terminal-Only** — Rich visual feedback, no GUIs.

When contributing, keep these principles in mind. If you're unsure whether a feature aligns with Swiss Knife's philosophy, open an [issue](https://github.com/yourusername/swiss-knife/issues) to discuss first.

---

## Setting Up Your Development Environment

### Prerequisites

- **Windows 11** (or Windows 10 with PowerShell 7+)
- **Git** ([Git for Windows](https://git-scm.com/download/win))
- **Conda** ([Miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html) or [Anaconda](https://www.anaconda.com/))

### Step 1: Clone and Navigate

```powershell
git clone https://github.com/yourusername/swiss-knife.git
cd swiss-knife
```

### Step 2: Create Conda Environment

```powershell
# Create a new Python 3.11 environment
conda create -n tools-env python=3.11

# Activate the environment
conda activate tools-env

# Install system dependencies (ffmpeg, pandoc)
conda install -c conda-forge ffmpeg pandoc
```

### Step 3: Install Swiss Knife in Editable Mode

```powershell
pip install -e .
```

This installs Swiss Knife in development mode, meaning the `knife` command reflects changes you make to the code immediately.

### Step 4: Verify Setup

```powershell
knife --list
```

You should see all available tools listed with brief descriptions.

---

## Adding a New Tool

### Overview

Each tool is a Python module in the `tools/` directory. The tool:
- Implements a `run()` function that serves as the CLI entry point
- Reads arguments via argparse
- Manages its own dependencies with the `_require()` helper
- Operates independently with no shared state between tools

### Step-by-Step Guide

#### 1. Use the Template

Copy `tools/_template.py` as your starting point:

```powershell
Copy-Item tools/_template.py tools/mytool.py
```

#### 2. Define the Tool's Interface

In your new `tools/mytool.py`, define the CLI arguments, flags, and help text. Edit the docstring and argparse setup to match your tool:

```python
"""
🔧 mytool — Brief one-line description

Extended description of what your tool does and the problem it solves.

Examples:
    knife mytool input.txt
    knife mytool file --output result.txt --option value
"""

def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife mytool",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Define your arguments
    parser.add_argument("input", help="Input file or path")
    parser.add_argument("--output", "-o", metavar="FILE", help="Output file")
    parser.add_argument("--flag", action="store_true", help="Some flag")
    
    args = parser.parse_args()
    
    # Your implementation
    ...
```

#### 3. Implement Core Logic

Move your tool's logic into one or more helper functions (not in `run()`). This keeps the CLI entry point clean and makes logic testable:

```python
def process_file(input_path: Path, option: str) -> str:
    """Core logic of your tool."""
    # Your implementation
    return result
```

#### 4. Handle Optional Dependencies

If your tool requires external packages, use the `_require()` helper to provide a clear error message if they're missing:

```python
def _require(package: str, pip_name: str | None = None):
    import importlib
    try:
        return importlib.import_module(package)
    except ImportError:
        pip_name = pip_name or package
        print(f"\033[31m✗ Missing dependency: '{package}'\033[0m")
        print(f"  Install with:  pip install {pip_name}")
        # For conda-forge packages:
        # print(f"  Install with:  conda install -c conda-forge {pip_name}")
        sys.exit(1)

def run() -> None:
    # ... argument parsing ...
    
    # Late import of optional dependencies
    lib = _require("some_library")
    result = lib.process(args.input)
    
    # ... output ...
```

#### 5. Use Rich for Visual Output

Use Rich or ANSI escape codes for colored, styled terminal output. Follow this convention:

- `yellow` or `\033[33m` — Progress/processing
- `green` or `\033[32m` — Success
- `red` or `\033[31m` — Error
- `cyan` or `\033[36m` — Information/file paths

```python
from rich.console import Console

console = Console()

# Progress
console.print(f"⏳ Processing: {input_file}", style="yellow")

# Success
console.print(f"✓ Complete: {result}", style="green")

# Error
console.print(f"✗ Error: {message}", style="red")

# Info
console.print(f"ℹ Info: {details}", style="cyan")
```

Or with ANSI codes:

```python
print(f"\033[33m⏳ Processing:\033[0m {input_file}")
print(f"\033[32m✓ Complete:\033[0m {result}")
print(f"\033[31m✗ Error:\033[0m {message}")
print(f"\033[36mℹ Info:\033[0m {details}")
```

#### 6. Register the Tool in `main.py`

Add your tool to the `TOOLS` dictionary in `main.py`:

```python
TOOLS: dict[str, tuple[str, str]] = {
    # ... existing tools ...
    "mytool": (
        "tools.mytool",
        "One-line description of your tool",
    ),
}
```

#### 7. Add Dependencies to `pyproject.toml`

If your tool uses external packages, add them to the `dependencies` list in `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing ...
    "package-name>=1.0.0",
]
```

#### 8. Test Your Tool

Reinstall the package to pick up the new registration:

```powershell
pip install -e .
```

Then test:

```powershell
knife --list          # See your tool listed
knife mytool --help   # View your tool's help
knife mytool input.txt # Run your tool
```

### Example: A Simple Word Count Tool

Here's a minimal but complete example:

```python
"""
🔧 wordcount — Count words, lines, and characters in a file

Examples:
    knife wordcount document.txt
    knife wordcount document.txt --output stats.txt
"""

import sys
import argparse
from pathlib import Path


def count_words(file_path: Path) -> dict[str, int]:
    """Count lines, words, and characters in a file."""
    text = file_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    words = text.split()
    chars = len(text)
    
    return {
        "lines": len(lines),
        "words": len(words),
        "chars": chars,
    }


def run() -> None:
    parser = argparse.ArgumentParser(
        prog="knife wordcount",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument("input", help="Input text file")
    parser.add_argument("--output", "-o", metavar="FILE", help="Save results to file")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"\033[31m✗ File not found: {input_path}\033[0m")
        sys.exit(1)
    
    print(f"\033[33m⏳ Counting:\033[0m {input_path.name}")
    
    stats = count_words(input_path)
    
    result = f"""
Lines:  {stats['lines']}
Words:  {stats['words']}
Chars:  {stats['chars']}
    """.strip()
    
    print(f"\033[32m✓ Results:\033[0m")
    print(result)
    
    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"\033[36m💾 Saved to: {Path(args.output).resolve()}\033[0m")
```

---

## Code Conventions

### Tool Structure

Every tool should follow this structure:

```python
"""
Brief description and usage examples.
"""

import sys
import argparse
from pathlib import Path


def _require(package: str, pip_name: str | None = None):
    """Helper to gracefully handle missing optional dependencies."""
    # (Already provided in _template.py)


def core_logic(input_path: Path, option: str) -> str:
    """Implement your tool's core logic in a named function, not in run()."""
    pass


def run() -> None:
    """CLI entry point. Parse args, call core logic, format output."""
    parser = argparse.ArgumentParser(
        prog="knife <toolname>",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # ... args and execution ...
```

### Important Rules

1. **No Shared State** — Tools should not import from each other or share global variables. Each tool is independent.

2. **No Logging Framework** — Use simple `print()` with colors, not logging modules. Keep it lightweight.

3. **No Tests or CI** — Tests are welcome, but not required. CI/CD is not set up.

4. **Rich or ANSI** — Use Rich for modern output, or ANSI escape codes for simplicity. Consistency is appreciated.

5. **Error Handling** — Validate input, show clear error messages, and exit with `sys.exit(1)`.

6. **Help Text** — Always provide a docstring with examples. Good help text saves users from the docs.

### Tool Naming

Use kebab-case for CLI tool names (e.g., `knife find-dup`), but snake_case for Python module names (e.g., `find_dup.py`). Register the correct mapping in `TOOLS`:

```python
TOOLS = {
    "find-dup": ("tools.find_dup", "description"),
}
```

---

## Code Review & PR Process

### Before You Submit

1. **Test your changes** — Run the tool manually and verify it works as expected.

2. **Update docs if needed** — If you add a new tool or change a tool's interface, update its docstring and this guide if appropriate.

3. **Keep PRs focused** — One feature or fix per PR. If you're adding a tool, don't refactor other tools in the same PR.

4. **Use clear commit messages** — Describe *why* you made the change, not just *what*.

   ✓ Good: `Add wordcount tool to count lines, words, and characters in files`
   
   ✗ Bad: `add new tool`

### Submitting a PR

1. **Fork the repository** on GitHub.

2. **Create a feature branch** from `main`:
   ```powershell
   git checkout -b feature/my-new-tool
   ```

3. **Make your changes** and commit with clear messages:
   ```powershell
   git commit -m "Add wordcount tool for text analysis"
   ```

4. **Push your branch**:
   ```powershell
   git push origin feature/my-new-tool
   ```

5. **Open a PR** on GitHub with a clear title and description:
   - **Title**: `Add wordcount tool` or `Fix bug in transcribe tool`
   - **Description**: Explain what you changed and why. Link related issues if any.

### What We Look For

- **Functionality** — Does the tool work as intended?
- **Code Quality** — Is it clean, readable, and following conventions?
- **Error Handling** — Does it gracefully handle bad input?
- **Documentation** — Is the docstring clear? Are examples provided?
- **Fit** — Does it align with Swiss Knife's philosophy (local-first, Windows native, single responsibility)?

---

## Ideas for Contribution

If you're looking for something to work on, here are some ideas:

### Easy First Issues

- Improve the lightweight tools: `fetch`, `find-dup`, `img-info`, `qr`, `compress`
  - Better error messages
  - More output options (JSON, CSV, etc.)
  - Performance improvements
  
- Add a new simple tool:
  - `hash` — Compute MD5, SHA-256, etc. of files
  - `rename-bulk` — Batch rename files with regex
  - `text-stats` — Analyze text (word frequency, readability, etc.)
  - `duration` — Get duration of audio/video files
  - `image-resize` — Batch resize images

### Medium Difficulty

- Cross-platform support (Linux, macOS) with conditional system binary paths
- Configuration file support (`.swissrc` for tool defaults)
- Better error messages and user guidance
- Performance optimizations for batch operations

### Advanced

- MCP Server integration — Expose Swiss Knife tools as an MCP server
- Async/parallel batch processing
- Plugin system for user-defined tools
- Interactive mode with autocomplete

---

## Questions or Issues?

- **Questions?** Open a [discussion](https://github.com/yourusername/swiss-knife/discussions).
- **Bug report?** Open an [issue](https://github.com/yourusername/swiss-knife/issues).
- **Security issue?** See [SECURITY.md](SECURITY.md).

---

## License

By contributing to Swiss Knife, you agree that your contributions will be licensed under the [MIT License](LICENSE).

Thank you for helping make Swiss Knife better!
