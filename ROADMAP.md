# Swiss Knife CLI — Roadmap

> **Philosophy:** One command replaces multiple browser tabs. Every tool lives in the terminal, composes with others, and — for tools marked with MCP — can be called directly by AI agents.

---

## Vision

Swiss Knife CLI evolves in three phases:

| Phase | Focus | Target |
|---|---|---|
| **Phase 1** | CLI improvements — richer features per tool | Current → v1.x |
| **Phase 2** | MCP server — expose tools to AI agents (Claude, Cursor) | v2.0 |
| **Phase 3** | Cross-platform — Linux/macOS support via conda-forge | v3.0 |

A future `knife-mcp-server` will run locally and register each tool with AI clients via `~/.claude/mcp.json`. The AI never receives raw binaries — only text transcripts, single frame images, metadata tables, and file paths.

---

## MCP Output Principle

> **Never send video, audio, or full PDFs to the model. Only send what the model can reason over.**

| Content type | MCP returns |
|---|---|
| Audio/video | Text transcript (markdown) |
| Video frame | Single JPEG image (base64) |
| Image result | PNG (base64) + description |
| PDF operations | File path + page count |
| Metadata | Markdown table |
| Crypto/encode | Plain text result |
| QR code | SVG or PNG (base64) — renders inline in Claude chat |

---

## Tool Roadmaps

---

### 1. `transcribe` — Audio/Video → Text

**Current state:** Chunked audio transcription via Google Speech, basic text output.

**CLI enhancements planned:**
- Speaker diarization — separate conversation by speaker (`Speaker A:`, `Speaker B:`)
- Multiple export formats: Markdown, SRT subtitles, JSON with timestamps
- Whisper local model support (offline, no API limit)
- Auto-detect language
- Progress bar per chunk

**MCP integration:**
- Tool: `knife_transcribe`
- Inputs: `file_path`, `format` (md|srt|json), `language` (auto|es|en|...)
- AI triggers transcription, receives the full transcript as markdown
- Model can then summarize, extract action items, or analyze the conversation
- Output in chat: formatted markdown with speaker labels and timestamps

---

### 2. `rembg` — Advanced Image Composition

**Current state:** Background removal from a single image via U2Net.

**CLI enhancements planned:**
- **Remove background** (already works): `knife rembg remove input.png`
- **Apply background**: `knife rembg apply foreground.png background.png` — composites fg onto bg
- **Solid color background**: `knife rembg apply input.png --bg-color #ffffff`
- **Blur background**: `knife rembg apply input.png --bg-blur 20`
- Batch mode: `knife rembg remove *.jpg`
- Output quality control: `--quality 90`

**MCP integration:**
- Tool: `knife_rembg`
- Inputs: `operation` (remove|apply), `foreground_path`, `background_path` (optional), `bg_color` (optional)
- Returns: base64 PNG image + dimensions + output path
- AI can request background removal and receive the result as an inline image in chat
- Useful for: product photo workflows, avatar creation, image editing automation

---

### 3. `crypto` — Cryptography & Encoding

**Current state:** Classic ciphers — César, Vigenère, Affine, Rail Fence, Columnar, Base64.

**CLI enhancements planned:**
- Explicit `--mode encrypt|decrypt` flag
- Frequency analysis helper (`--attack frequency`)
- Brute-force mode for César and short Vigenère keys
- Known-plaintext attack helper
- Output entropy score

**MCP integration:**
- Tool: `knife_crypto`
- Inputs: `cipher`, `mode`, `text`, `key` (optional), `attack` (optional)
- Returns: result text + key used (if brute-forced) + entropy info
- Useful for: CTF assistance, educational demos, encoding/decoding in agent workflows
- Output in chat: code block with result, cipher details as markdown

---

### 4. `convert` — Multi-Format Converter

**Current state:** Audio, video, doc, data, markup conversion. Windows-native via Word COM + pandoc.

**CLI enhancements planned:**
- Cross-OS backend detection: Word COM (Windows) → LibreOffice → pandoc, in order of availability
- Explicit `--backend` flag to force a specific converter
- Better batch support: `knife convert *.docx --to pdf`
- Format autodetection from extension
- Conversion report: input size → output size, time taken
- Add: Markdown → DOCX, HTML → PDF (via pandoc), JSON → CSV

**MCP integration:**
- Tool: `knife_convert`
- Inputs: `input_path`, `output_format`, `backend` (optional)
- Returns: output file path + format + size comparison
- AI can convert documents as part of processing workflows
- Output in chat: structured text with input/output info

---

### 5. `clip` — Video Editor

**Current state:** Lossless trim by timestamp via ffmpeg stream copy.

**CLI enhancements planned:**
- **Join/concatenate** multiple videos: `knife clip join a.mp4 b.mp4 c.mp4 -o out.mp4`
- **Add audio track** to video at a given timestamp offset: `knife clip add-audio video.mp4 audio.mp3 --offset 00:30`
- **Basic transitions** between clips (fade, crossfade): `knife clip join a.mp4 b.mp4 --transition fade`
- **Extract frame** as image: `knife clip frame video.mp4 --at 01:23 -o frame.jpg`
- **Trim**: `knife clip trim video.mp4 --start 00:30 --end 01:45`

**MCP integration:**
- Tools: `knife_clip_trim`, `knife_clip_join`, `knife_clip_frame`, `knife_clip_add_audio`
- **Critical principle:** when the AI needs to "see" a moment in a video, `knife_clip_frame` returns a single JPEG frame as base64 — never the video itself
- AI can suggest edit points, the user confirms, the MCP executes
- Output in chat: frame image (inline) + metadata (duration, resolution, fps) as markdown table
- Editing workflow: AI gets frames → analyzes → suggests cuts → user approves → MCP executes → returns preview frame

---

### 6. `compress` — Image & Video Compression

**Current state:** Basic Pillow image compression + libx265 video compression.

**CLI enhancements planned:**
- Quality presets: `--quality low|medium|high|lossless`
- Before/after size comparison table in output
- Batch processing: `knife compress *.jpg --quality medium`
- Target file size mode: `--target-size 500kb` (auto-adjusts quality)
- Lossless PNG optimization via optipng/oxipng

**MCP integration:** Not planned for Phase 2. CLI-only tool.

---

### 7. `merge-pdf` — Full PDF Control

**Current state:** Merge multiple PDFs (PyPDF2).

**CLI enhancements planned:**
- **Merge**: `knife merge-pdf a.pdf b.pdf c.pdf -o out.pdf` (already works)
- **Split by page range**: `knife merge-pdf split input.pdf --ranges 1-3,4-10`
- **Extract pages**: `knife merge-pdf extract input.pdf --pages 1,3,5-8`
- **Delete pages**: `knife merge-pdf delete input.pdf --pages 2,5`
- **Rotate pages**: `knife merge-pdf rotate input.pdf --pages 1-3 --angle 90`
- All operations via `pypdf` (modern PyPDF2 fork)

**MCP integration:**
- Tools: `knife_pdf_merge`, `knife_pdf_split`, `knife_pdf_extract`, `knife_pdf_delete`
- Inputs: file paths + page ranges
- Returns: output file path + page count + operation summary
- AI never receives PDF content — only metadata and file paths
- Output in chat: operation result as markdown (pages processed, output path, file size)

---

### 8. `fetch` — Clean URL Text Extraction

**Current state:** Basic BeautifulSoup text extraction from URLs.

**CLI enhancements planned:**
- Better article extraction via `trafilatura` or `newspaper3k` as optional backends
- Handle JS-heavy sites via `requests-html` (optional)
- Output formats: plain text, markdown, JSON (title + body + links)
- `--no-links` / `--links-only` flags
- Readability mode: strip nav, ads, footers

**MCP integration:** Not planned. AI models already browse effectively. CLI-only tool.

---

### 9. `find-dup` — Duplicate File Detection

**Current state:** SHA-256 hash duplicate detection.

**CLI enhancements planned:**
- Group duplicates in output (show which files are identical)
- Show file sizes alongside paths
- `--delete` mode: keep newest/oldest, delete the rest (with confirmation)
- Recursive directory scan: `knife find-dup ~/Downloads --recursive`
- Output as JSON for piping: `knife find-dup . --json`

**MCP integration:** Not planned. CLI-only tool.

---

### 10. `img-info` — Metadata Manager

**Current state:** EXIF metadata extraction from images (Pillow).

**CLI enhancements planned:**
- **Read** EXIF/XMP/IPTC from images (already works)
- **Write/inject** metadata: `knife img-info write photo.jpg --title "Sunset" --author "Mao"`
- **Strip all metadata** (privacy): `knife img-info strip photo.jpg`
- **Expand to other formats**: MP4 video metadata, PDF properties, DOCX author/revision
- Batch mode: `knife img-info read *.jpg --format table`
- GPS coordinate display on a map link

**MCP integration:**
- Tool: `knife_img_info`
- Inputs: `file_path`, `operation` (read|write|strip), `metadata` (dict, for write)
- Returns: metadata as a markdown table (formatted for chat)
- AI can read metadata to understand file context, or strip metadata before sharing
- Output in chat: rich markdown table with all fields

---

### 11. `qr` — Advanced QR Code Generator

**Current state:** Basic QR code generation.

**CLI enhancements planned:**
- Custom colors: `--fg-color #000000 --bg-color #ffffff`
- Embed logo/image in center: `--logo logo.png`
- Error correction levels: `--ecc L|M|Q|H`
- Output formats: PNG, SVG
- QR styles: rounded corners, dot pattern (`--style rounded|dots|classic`)
- Size control: `--size 400` (pixels)
- Batch: generate from CSV of URLs

**MCP integration:**
- Tool: `knife_qr`
- Inputs: `content`, `format` (png|svg), `style`, `fg_color`, `bg_color`, `logo_path` (optional)
- Returns: base64-encoded PNG or SVG string — **renders inline in Claude chat**
- The QR code appears visually in the conversation without saving to disk
- AI can generate QR codes on demand as part of content creation workflows
- Output in chat: inline image (PNG) + text confirmation of content encoded

---

## Potential New Tools

> Research completed. See [Tool Recommendations](#) section below.

| Name | Description | MCP | Priority |
|---|---|---|---|
| `transform` | JSON ↔ YAML ↔ TOML ↔ CSV conversion | Yes | High |
| `encode` | Base64/URL/HTML/JWT encode-decode | No | High |
| `rename` | Bulk rename with regex + preview | Yes | High |
| `password` | Secure password/UUID/passphrase generator | No | High |
| `http` | API request tool (lightweight httpie) | Yes | High |
| `ocr` | Extract text from images/scanned PDFs | Yes (high) | Medium |
| `diff` | Colored file diff (unified/side-by-side) | Yes | Medium |
| `summarize` | Summarize docs/URLs via LLM | Yes (high) | Medium |
| `translate` | Translate text/files between languages | Yes (high) | Medium |
| `fake` | Generate realistic test data (names, emails, etc.) | Yes | Medium |
| `csv` | Filter/sort/join CSV with SQL-like syntax | Yes | Medium |
| `hash` | Hash strings or files (MD5/SHA/BLAKE2) | No | High |
| `strip-meta` | Strip metadata from any file type (privacy) | No | Medium |
| `sort-files` | Organize files into folders by date/type | Yes | Medium |
| `watch` | Watch files/dirs and trigger commands on change | No | Medium |

---

## Phase Timeline

### Phase 1 — CLI Improvements (v1.x)

Priority order based on complexity and impact:

1. `merge-pdf` — add split/extract/delete (Easy, high impact)
2. `qr` — custom colors, logo, SVG output (Easy)
3. `img-info` — metadata write + strip (Medium)
4. `clip` — join videos + extract frame (Medium)
5. `compress` — quality presets + batch (Easy)
6. `convert` — cross-OS backend detection (Medium)
7. `transcribe` — Whisper local + SRT export (Medium)
8. `rembg` — background apply/composite (Medium)
9. New: `transform`, `encode`, `password`, `hash` (Easy, high ROI)

### Phase 2 — MCP Server (v2.0)

- `knife-mcp-server.py` using official `mcp` Python SDK
- Expose: transcribe, rembg, crypto, convert, clip, merge-pdf, img-info, qr
- Rich output: text (markdown), images (base64), structured JSON
- Registration via `~/.claude/mcp.json` for Claude Desktop + Claude Code
- Security: local-only, file validation, no shell execution

### Phase 3 — Cross-Platform (v3.0)

- Conda environment works on Linux/macOS already (most tools)
- Replace Windows-specific: `docx2pdf` (Word COM) → LibreOffice on Linux
- `setup.sh` reactivated and maintained alongside `setup.ps1`
- PyPI distribution: `pip install swiss-knife-cli`
