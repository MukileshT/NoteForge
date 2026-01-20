# Quick Start Guide

## For End Users (Executable)

### Step 1: Download
Download `ObsidianNotesConverter.exe` from the releases page.

### Step 2: First Run
1. Double-click `ObsidianNotesConverter.exe`
2. The application will open with a GUI

### Step 3: Basic Usage (No API Keys Required)
1. Click "Select PDF/Images" - choose your files
2. Click "Select Vault" - choose your Obsidian vault folder
3. Make sure "Local" OCR mode is selected
4. Click "Start Processing"
5. Your notes will appear in the vault!

### Step 4: Optional - Add API Keys for AI Features
1. Click "Manage API Keys"
2. Add keys for any provider:
   - Gemini (recommended): Free tier available
   - OpenAI: Requires paid account
   - Anthropic: Requires paid account
   - Groq: Free tier available
3. Enable "LLM Refinement" for better text cleaning
4. Select "AI" OCR mode for better accuracy

---

## For Developers

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd obsidian_notes_converter

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Project Structure
```
obsidian_notes_converter/
├── config/              # Configuration files
│   ├── app_config.json  # Main config
│   └── symbols.json     # Symbol definitions
├── data/                # Reference data
├── src/                 # Source code
│   ├── core/            # Core pipeline
│   ├── gui/             # GUI components
│   ├── llm/             # LLM providers
│   ├── ocr/             # OCR engines
│   ├── preprocessing/   # PDF/image processing
│   ├── processing/      # Text processing
│   ├── vision/          # Vision/diagram detection
│   └── vault/           # Obsidian vault operations
├── main.py              # Entry point
└── requirements.txt     # Dependencies
```

### Build Executable

```bash
# Clean development files
cleanup.bat

# Build executable
build.bat

# Result: dist/ObsidianNotesConverter.exe
```

### Development Workflow

1. **Make changes** to source files
2. **Test** with `python main.py`
3. **Clear cache** if needed: Delete `__pycache__` folders
4. **Build** with `build.bat`
5. **Test executable** in `dist/`

### Common Development Tasks

#### Add a new LLM provider
1. Edit `src/llm/provider_factory.py`
2. Add provider configuration
3. Test with API key

#### Modify OCR behavior
1. Edit `src/ocr/ocr_manager.py`
2. Adjust confidence thresholds
3. Test with sample files

#### Change UI
1. Edit `src/gui/enhanced_main_window.py`
2. Test with `python main.py`

---

## Tips for Best Results

### For Handwritten Notes
- Use high-resolution scans (300 DPI minimum)
- Ensure good lighting and contrast
- Enable "LLM Refinement" for better text cleanup
- Consider using AI OCR mode for better accuracy

### For Printed Documents
- Local OCR works well for most printed text
- Use AI OCR for complex layouts or multiple languages
- Enable diagram detection for charts and graphs

### For Large Documents
- Process in batches of 10-20 pages
- Use Local OCR to save API costs
- Close other applications to free memory

### API Cost Optimization
- Use Local OCR when possible (free)
- Only enable LLM Refinement when needed
- Groq and Gemini offer generous free tiers
- Monitor usage with quota tracking in the app

---

## Troubleshooting

### Application won't start
- Ensure Windows 10/11 64-bit
- Install Visual C++ Redistributable
- Run as administrator if needed

### OCR not working
- Check internet connection (for AI mode)
- Verify API keys (for AI mode)
- Try switching between Local and AI modes
- Check logs in `logs/` folder

### Low quality output
- Increase input image quality
- Enable LLM Refinement
- Try AI OCR mode
- Adjust confidence threshold in config

### Out of memory
- Process fewer pages at once
- Use AI OCR (lower memory than local)
- Close other applications
- Restart the application

---

## Getting Help

1. Check [INSTALL.md](INSTALL.md) for detailed installation help
2. Review [README.md](README.md) for features and configuration
3. Check logs in `logs/` folder for error details
4. Create an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Log files
   - System information

---

## What's Next?

- ⭐ Star the project if you find it useful
- 🐛 Report bugs or request features
- 🤝 Contribute improvements
- 📖 Share your experience

Happy converting! 🚀
