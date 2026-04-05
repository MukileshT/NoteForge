# NoteForge

NoteForge converts PDFs and images into Markdown notes for Obsidian.

## Overview

- Local OCR with PaddleOCR and EasyOCR
- Optional AI OCR with OpenAI, Anthropic, Gemini, and Groq
- Direct export into an Obsidian vault
- Encrypted storage for API keys

## Run from Source

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Build for Windows

```bash
build.bat
```

The executable is created in `dist\NoteForge.exe`.

## Key Storage

Encrypted API keys are stored under the NoteForge app data folder:

`%APPDATA%\NoteForge\keys.enc`

The master key is stored alongside it as:

`%APPDATA%\NoteForge\master.key`

## Requirements

- Windows 10 or 11
- Python 3.10 or newer for source usage

## Author

Mukilesh T
