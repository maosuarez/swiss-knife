# Swiss Knife CLI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%2011-0078d4.svg)](https://www.microsoft.com/en-us/windows/windows-11)
[![Terminal: PowerShell](https://img.shields.io/badge/terminal-PowerShell-5391FE.svg)](https://github.com/PowerShell/PowerShell)

> **Stop context-switching between browser tabs, online converters, and multi-step manual workflows.**
> 
> Swiss Knife is a no-frills CLI tool suite that brings essential productivity operations directly to your Windows Terminal—transcribe audio, remove image backgrounds, convert formats, compress media, extract metadata, and more. All 100% local, no cloud, no bloat.

---

## Quick Start

### Installation

Swiss Knife requires **Python 3.11+** and **conda** (for system dependencies like ffmpeg).

```powershell
# 1. Clone the repository
git clone https://github.com/yourusername/swiss-knife.git
cd swiss-knife

# 2. Create a conda environment with system dependencies
conda create -n tools-env python=3.11
conda activate tools-env
conda install -c conda-forge ffmpeg pandoc

# 3. Install Swiss Knife in editable mode
pip install -e .

# 4. Verify installation
knife --list
```

The `knife` command is now available in your PowerShell terminal when the `tools-env` environment is active.

### Usage

```powershell
# List all tools
knife --list

# Get help for a specific tool
knife <tool> --help

# Run a tool
knife transcribe audio.mp3
knife convert document.docx --to pdf
knife clip video.mp4 --start 00:30 --end 01:45
```

---

## Tools

| Tool | Purpose | Example |
|------|---------|---------|
| **transcribe** | Audio/video to text with timestamps and speaker diarization | `knife transcribe meeting.mp4 --output transcript.md` |
| **rembg** | Remove image backgrounds using local AI | `knife rembg photo.jpg` |
| **crypto** | Encrypt/decrypt with classic ciphers | `knife crypto --encrypt "hello" --cipher caesar --key 3` |
| **convert** | Convert documents, audio, video, images, and data formats | `knife convert doc.docx --to pdf` |
| **clip** | Lossless audio/video trimming by timestamp | `knife clip video.mp4 --start 00:30 --end 01:45` |
| **compress** | Compress images and videos | `knife compress video.mp4 --quality medium` |
| **merge-pdf** | Combine multiple PDF files | `knife merge-pdf file1.pdf file2.pdf --output merged.pdf` |
| **fetch** | Download a URL as clean plain text | `knife fetch https://example.com --output page.txt` |
| **find-dup** | Detect duplicate files by SHA-256 hash | `knife find-dup ./documents` |
| **img-info** | Extract EXIF metadata from images | `knife img-info photo.jpg` |
| **qr** | Generate QR codes | `knife qr "https://example.com" --output code.png` |

---

## Features

- **100% Local Processing** — No cloud dependencies, no tracking, no rate limits. Everything runs on your machine.
- **Zero Context-Switching** — One unified CLI dispatches to all tools. No more hunting for browser converters.
- **Windows Native** — Built for PowerShell and Windows Terminal. Conda ensures system binaries (ffmpeg, pandoc) just work.
- **Rich Terminal Output** — Color-coded progress, success messages, and error feedback.
- **Batch Operations** — Many tools support processing multiple files in one command.
- **MIT Licensed** — Free to use, modify, and redistribute.

---

## Architecture

Swiss Knife follows a modular dispatcher pattern:

```
knife (main CLI entry point in main.py)
├── tools/
│   ├── transcribe.py
│   ├── rembg_tool.py
│   ├── encryption.py
│   ├── convert.py
│   ├── clip.py
│   ├── compress.py
│   ├── merge_pdf.py
│   ├── fetch.py
│   ├── find_dup.py
│   ├── img_info.py
│   └── qr.py
└── pyproject.toml (defines entry point: knife = "main:main")
```

Each tool is a **standalone Python module** that:
- Exposes exactly one `run()` function as its CLI entry point
- Reads arguments via argparse from `sys.argv`
- Has no shared state with other tools
- Manages its own dependencies using the `_require()` pattern

This design ensures tools are independent, testable, and easy to add or modify without affecting others.

---

## Development

### Setting Up a Development Environment

Follow the same steps as installation, but clone your fork instead:

```powershell
git clone https://github.com/yourusername/swiss-knife.git
cd swiss-knife
conda create -n tools-env python=3.11
conda activate tools-env
conda install -c conda-forge ffmpeg pandoc
pip install -e .
```

### Adding a New Tool

See [CONTRIBUTING.md](CONTRIBUTING.md) for a detailed guide on adding new tools.

### Code Conventions

- **Visual Output**: Use Rich or ANSI escape codes for colored, styled terminal output (`yellow` for progress, `green` for success, `red` for error, `cyan` for info).
- **Optional Dependencies**: Use the `_require()` helper to gracefully handle missing optional packages.
- **Tool Isolation**: Tools should not depend on each other. Use only their own argparse and internal helpers.
- **No Shared State**: Avoid modifying global variables or creating shared modules between tools.

For complete conventions, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## Roadmap

- **MCP Server Integration** — Expose Swiss Knife as an MCP server so AI agents can invoke tools programmatically.
- **Cross-Platform Support** — Linux and macOS with fallbacks for system binaries (ffmpeg, pandoc).
- **Plugin System** — Allow users to register custom tools without modifying the core codebase.
- **Async/Parallel Processing** — Speed up batch operations by processing multiple files concurrently.
- **Configuration Files** — Support `.swissrc` or similar for tool defaults and presets.

---

## Contributing

We welcome contributions! Whether you want to:
- Add a new tool
- Improve an existing tool
- Fix a bug
- Improve documentation

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines, including setup instructions and the PR process.

---

## Security

If you discover a security vulnerability, please consult [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## License

Swiss Knife is released under the [MIT License](LICENSE). You're free to use, modify, and distribute it, even commercially.

---

## Author

Created and maintained by [Mao Suárez](https://github.com/maosuarezbarrer).

---

## Acknowledgments

Swiss Knife builds on excellent open-source libraries:
- [Whisper](https://github.com/openai/whisper) for audio transcription
- [rembg](https://github.com/danielgatis/rembg) for background removal
- [Rich](https://github.com/Textualize/rich) for terminal styling
- [ffmpeg](https://ffmpeg.org/) for media processing
- And many others ([see requirements](pyproject.toml))

---

**Questions?** Open an [issue](https://github.com/yourusername/swiss-knife/issues) or start a [discussion](https://github.com/yourusername/swiss-knife/discussions).
