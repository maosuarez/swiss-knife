# Swiss Knife MCP Server

Architecture, tool schemas, output format guide, and implementation roadmap for the Swiss Knife MCP (Model Context Protocol) server.

---

## 1. Overview

The Swiss Knife MCP server exposes `knife` CLI tools as callable tools for AI models (Claude Desktop, Claude Code, Cursor, etc.). Instead of `knife transcribe audio.mp3` in a terminal, an AI agent calls `knife_transcribe` directly, receives structured output, and reasons over the result in the same conversation turn.

The server runs **locally on the user's machine**. No data leaves the machine except where explicitly noted (Google Speech in `transcribe`). The AI model calls the server over a local socket — all processing happens on disk.

**Exposed via MCP (8 tools):** `transcribe`, `rembg`, `crypto`, `convert`, `clip`, `merge-pdf`, `img-info`, `qr`

**CLI-only (no MCP):** `fetch`, `find-dup`, `compress`

> Rationale for exclusions: `fetch` returns unpredictable volumes of scraped text — AI models browse better natively. `find-dup` output is terminal-oriented lists with no structured result the model benefits from. `compress` is a batch operation without a meaningful result to reason over.

---

## 2. Output Format Guide

MCP responses are lists of **content blocks**. Each block has a `type` and type-specific fields. This is what enables rich rendering inside the AI chat interface.

### 2.1 Text Content

```
type: "text"
field: text (string — any length, supports full Markdown)
```

Renders as: formatted Markdown in Claude's chat. Headers, tables, bold, code blocks, lists all render natively.

**Use for:** transcripts, metadata tables, operation results, cipher output, conversion status.

### 2.2 Image Content

```
type: "image"
fields: data (base64-encoded bytes), mimeType ("image/png" | "image/jpeg")
```

Renders as: **inline image in Claude's chat**. The model can visually analyze the content.

**Use for:** background-removed PNGs, QR codes, video frame extracts, processed images.

Size constraint: keep under 5 MB base64-encoded. For larger results, return a file path in a text block instead.

### 2.3 Multiple Content Blocks (text + image)

A single tool call can return both text and image blocks together. This is the most powerful pattern — the AI sees both the result and can reason about it.

| Pattern | Tools that use it |
|---|---|
| `text + image` | `rembg`, `qr`, `knife_clip_extract_frame` |
| `text only` | `transcribe`, `crypto`, `convert`, `merge-pdf`, `img-info` |

### 2.4 What NOT to Return

| File type | Do NOT return | Return instead |
|---|---|---|
| Audio/video | Binary file | Text transcript or single frame JPEG |
| PDF | Binary content | Operation status + output file path |
| Large images (>5MB) | Raw base64 | Resized thumbnail (base64) + file path |
| Any binary | Raw bytes | File path on disk |

> **Core principle:** The model never receives a video. It receives a frame. It never receives audio. It receives a transcript. It never receives a PDF. It receives metadata and a file path.

---

## 3. Tool Catalog

| MCP Tool Name | Source | Output | Description |
|---|---|---|---|
| `knife_transcribe` | `transcribe` | text (markdown) | Transcribe audio/video → timestamped markdown with speaker labels |
| `knife_rembg` | `rembg` | text + image (PNG) | Remove or apply background; return processed image inline |
| `knife_crypto` | `crypto` | text | Encrypt, decrypt, or attack a classical cipher |
| `knife_convert` | `convert` | text | Convert file between formats; return output path + stats |
| `knife_clip` | `clip` | text | Trim video/audio by timestamp; return output path + duration |
| `knife_clip_extract_frame` | `clip` + ffmpeg | image (JPEG) | Extract a single frame at a timestamp — for AI visual analysis |
| `knife_clip_join` | `clip` | text | Concatenate multiple video files; return output path |
| `knife_pdf_merge` | `merge-pdf` | text | Merge PDFs; return output path + page count |
| `knife_pdf_split` | `merge-pdf` | text | Split PDF by page ranges; return output paths |
| `knife_pdf_extract` | `merge-pdf` | text | Extract specific pages to new PDF |
| `knife_img_info` | `img-info` | text (table) | Read EXIF/XMP metadata as a markdown table |
| `knife_qr` | `qr` | text + image (PNG) | Generate QR code and return it rendered inline in chat |

---

## 4. Tool Schemas

### `knife_transcribe`

**Description:** Transcribe audio or video to text. Returns a markdown-formatted transcript with timestamps and speaker labels. The model receives text, not audio.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file_path` | string | Yes | Path to audio/video file |
| `format` | string | No | Output format: `md` (default), `srt`, `json` |
| `language` | string | No | Language code: `auto` (default), `es`, `en`, etc. |
| `speaker_separation` | boolean | No | Attempt speaker diarization (default: true) |

**Output:** `text` block — markdown with timestamps and speaker labels
**Example output in chat:**
```
**[00:00:05] Speaker A:** Welcome to the meeting.
**[00:00:09] Speaker B:** Thanks for having me.
```

---

### `knife_rembg`

**Description:** Remove or replace the background of an image. Returns the processed image inline in chat.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `foreground_path` | string | Yes | Path to the subject image |
| `operation` | string | No | `remove` (default) or `apply` |
| `background_path` | string | No | Path to background image (for `apply`) |
| `bg_color` | string | No | Hex color for solid background (e.g., `#ffffff`) |

**Output:** `text` block (path + dimensions) + `image` block (base64 PNG)

---

### `knife_crypto`

**Description:** Encrypt, decrypt, or attack a message using classical ciphers.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Input text |
| `cipher` | string | Yes | `caesar`, `vigenere`, `affine`, `railfence`, `columnar`, `base64` |
| `mode` | string | Yes | `encrypt`, `decrypt`, `attack` |
| `key` | string | No | Cipher key (not required for `attack` mode) |

**Output:** `text` block — cipher result in a code block + key info if brute-forced

---

### `knife_convert`

**Description:** Convert a file from one format to another.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `input_path` | string | Yes | Source file path |
| `output_format` | string | Yes | Target format (e.g., `pdf`, `mp3`, `csv`) |
| `backend` | string | No | Force specific backend: `word`, `libreoffice`, `pandoc`, `ffmpeg` |

**Output:** `text` block — output file path, input/output size, time taken

---

### `knife_clip`

**Description:** Trim audio or video by time range without re-encoding.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file_path` | string | Yes | Source video/audio file |
| `start` | string | Yes | Start time: `HH:MM:SS`, `MM:SS`, or seconds |
| `end` | string | Yes | End time: `HH:MM:SS`, `MM:SS`, or seconds |

**Output:** `text` block — output path + clip duration

---

### `knife_clip_extract_frame`

**Description:** Extract a single frame from a video at a specific timestamp. Use this when the AI needs to visually analyze a moment in a video. Never returns the video itself.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file_path` | string | Yes | Source video file |
| `timestamp` | string | Yes | Frame timestamp: `HH:MM:SS`, `MM:SS`, or seconds |
| `quality` | integer | No | JPEG quality 1-100 (default: 85) |

**Output:** `text` block (timestamp + video metadata) + `image` block (base64 JPEG)

> **AI video analysis workflow:** AI requests frame at timestamp → sees image → decides whether to extract more frames or proceed with edits → requests `knife_clip` for the actual cut.

---

### `knife_pdf_merge` / `knife_pdf_split` / `knife_pdf_extract`

**Description:** Full PDF manipulation — merge, split, or extract pages.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `files` | list[string] | Yes (merge) | List of PDF paths to merge |
| `input_path` | string | Yes (split/extract) | Source PDF |
| `ranges` | string | No | Page ranges: `1-3,5,7-10` |
| `output_path` | string | No | Output file path |

**Output:** `text` block — operation result, output path, page count

---

### `knife_img_info`

**Description:** Read, write, or strip image metadata (EXIF/XMP/IPTC).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `file_path` | string | Yes | Image file path |
| `operation` | string | No | `read` (default), `write`, `strip` |
| `metadata` | object | No | Key-value pairs to write (for `write` mode) |

**Output:** `text` block — markdown table of all metadata fields

---

### `knife_qr`

**Description:** Generate a QR code and return it as an inline image in chat.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `content` | string | Yes | URL, text, or data to encode |
| `format` | string | No | `png` (default) or `svg` |
| `fg_color` | string | No | Foreground hex color (default: `#000000`) |
| `bg_color` | string | No | Background hex color (default: `#ffffff`) |
| `ecc` | string | No | Error correction: `L`, `M` (default), `Q`, `H` |
| `style` | string | No | `classic` (default), `rounded`, `dots` |
| `logo_path` | string | No | Path to logo image to embed in center |

**Output:** `text` block (content encoded + settings) + `image` block (base64 PNG — **renders inline in Claude chat**)

---

## 5. Security Model

| Concern | Approach |
|---|---|
| **Data locality** | All processing happens on-disk locally. No data sent remotely except Google Speech (transcribe, opt-in) |
| **File access** | Tools only read/write files explicitly passed as arguments. No directory traversal. |
| **No shell execution** | Tools call Python APIs directly. No `subprocess` with user-controlled strings. |
| **No arbitrary commands** | The MCP server does not expose a general shell executor. |
| **Input validation** | File paths validated for existence and expected extension before processing. |
| **Rate limiting** | Expensive tools (`rembg`, `transcribe`) should be rate-limited in the server config. |

---

## 6. Implementation Approach

### Stack

```
pip install mcp          # Official MCP Python SDK (Anthropic)
```

### Server Entry Point

```
swiss-knife/
├── knife_mcp_server.py  # MCP server — new file
└── tools/               # Reuse existing tool modules internally
```

Each MCP tool is an `async` function decorated with `@server.tool()`. It calls the existing tool module logic directly (no re-implementation). Example structure:

```python
# knife_mcp_server.py (pseudocode — not final)
from mcp.server import Server
from mcp.types import TextContent, ImageContent

server = Server("swiss-knife")

@server.tool()
async def knife_qr(content: str, format: str = "png", ...) -> list:
    # Call existing qr tool logic
    img_bytes = generate_qr(content, format=format, ...)
    b64 = base64.b64encode(img_bytes).decode()
    return [
        TextContent(type="text", text=f"QR code generated for: {content}"),
        ImageContent(type="image", data=b64, mimeType="image/png"),
    ]
```

### Registration

**Claude Desktop / Claude Code** (`~/.claude/mcp.json` or via `/mcp` command):

```json
{
  "mcpServers": {
    "swiss-knife": {
      "command": "python",
      "args": ["C:/Users/maosu/Programas/swiss-knife/knife_mcp_server.py"],
      "env": {
        "CONDA_PREFIX": "C:/Users/maosu/miniconda3/envs/tools-env"
      }
    }
  }
}
```

**Alternative (via conda run):**

```json
{
  "mcpServers": {
    "swiss-knife": {
      "command": "conda",
      "args": ["run", "-n", "tools-env", "python",
               "C:/Users/maosu/Programas/swiss-knife/knife_mcp_server.py"]
    }
  }
}
```

---

## 7. Implementation Roadmap

### Phase 2.0 — Core MCP Server

1. Set up `knife_mcp_server.py` with `mcp` SDK
2. Implement `knife_qr` (easiest — returns image directly)
3. Implement `knife_img_info` (returns markdown table)
4. Implement `knife_crypto` (returns text)
5. Implement `knife_pdf_merge` / `knife_pdf_split`

### Phase 2.1 — Media Tools

6. Implement `knife_transcribe` (transcript as markdown)
7. Implement `knife_clip_extract_frame` (single frame as JPEG base64)
8. Implement `knife_clip` + `knife_clip_join`

### Phase 2.2 — Image AI Tools

9. Implement `knife_rembg` (PNG base64 return)
10. Implement `knife_convert`

### Phase 2.3 — Quality & Distribution

11. Add rate limiting for expensive ops
12. Write integration tests for each MCP tool
13. Publish server config in README for Claude Desktop + Claude Code setup
