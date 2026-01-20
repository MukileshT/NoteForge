# Obsidian Notes Converter

Convert PDFs and images to Obsidian markdown notes with OCR and AI assistance.

## 🚀 Quick Start

### Download Pre-built Executable
1. Download `ObsidianNotesConverter.exe` from [Releases](../../releases)
2. Double-click to run
3. Start converting your notes!

### Or Run from Source
```bash
# 1. Clone the repository
git clone <repository-url>
cd obsidian_notes_converter

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

## ✨ Features

- 📄 **PDF & Image Processing** - Convert PDFs and images to markdown
- 🔍 **Local OCR** - PaddleOCR and EasyOCR (no API required)
- 🤖 **AI-Powered OCR** - GPT-4, Claude, Gemini vision models
- 📊 **Diagram Detection** - Automatically detect and extract diagrams
- 🔗 **Smart Cross-Referencing** - Link related content automatically
- 📝 **Obsidian Integration** - Direct vault writing with proper formatting
- 💾 **No Cloud Required** - Works completely offline with local OCR

## 📋 Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 2GB free space
- **Python**: 3.10+ (only for source installation)

## 🔧 Configuration

### OCR Modes
- **Local OCR** (Default) - Free, no API keys needed
  - PaddleOCR for handwritten text
  - EasyOCR for printed text
- **AI OCR** - Requires API key, better accuracy
  - Supports: OpenAI, Anthropic, Gemini, Groq

### API Keys (Optional)
Configure through the Settings menu:
- Gemini: https://makersuite.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/
- Groq: https://console.groq.com/

## 📖 Documentation

- [Installation Guide](INSTALL.md) - Detailed setup instructions
- [Configuration](config/README.md) - Advanced configuration options

## 🛠️ Building Executable

To build your own executable:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run build script
build.bat

# Or manually:
pip install pyinstaller
pyinstaller build_exe.spec
```

Executable will be in `dist\ObsidianNotesConverter.exe`

## 🐛 Troubleshooting

### Common Issues

**PaddleOCR not working**
- Install Visual C++ Redistributable: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Use EasyOCR or AI OCR instead

**Out of memory**
- Process fewer pages at once
- Close other applications
- Use AI OCR mode (lower memory)

**API errors**
- Verify API key is correct
- Check quota/credits
- Ensure internet connection

See [INSTALL.md](INSTALL.md) for more troubleshooting help.

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## ⭐ Support

If this project helps you, please consider giving it a star!
