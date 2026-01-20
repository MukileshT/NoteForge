# Obsidian Notes Converter - Installation Guide

## Quick Install

### Option 1: Use Pre-built Executable (Recommended)
1. Download `ObsidianNotesConverter.exe` from the releases page
2. Double-click to run
3. Configure your API keys in Settings (optional for AI features)

### Option 2: Install from Source
1. **Prerequisites:**
   - Python 3.10 or higher
   - Git (optional)

2. **Installation:**
   ```bash
   # Clone or download this repository
   git clone <repository-url>
   cd obsidian_notes_converter

   # Create virtual environment
   python -m venv .venv

   # Activate virtual environment
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Run the application
   python main.py
   ```

## Configuration

### API Keys (Optional)
API keys are only needed if you want to use AI features. The application works with local OCR without any API keys.

Add your API keys through the Settings menu:
- **Gemini** (Google): Get from https://makersuite.google.com/app/apikey
- **OpenAI**: Get from https://platform.openai.com/api-keys
- **Anthropic**: Get from https://console.anthropic.com/
- **Groq**: Get from https://console.groq.com/

### OCR Modes
The application supports two OCR modes:
- **Local OCR** (Default): Uses PaddleOCR and EasyOCR (free, no API required)
- **AI OCR**: Uses vision models (requires API key, more accurate)

## Usage

1. **Select Files**: Click "Select PDF/Images" and choose your files
2. **Choose Vault**: Select your Obsidian vault location
3. **Select OCR Mode**: 
   - Local (free, no API needed)
   - AI (requires API key)
4. **Optional**: Enable LLM Refinement for better text cleaning
5. **Click "Start Processing"**
6. **Find Notes**: Your converted notes will be in the vault!

## System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 4GB
- **Disk Space**: 2GB free space
- **Display**: 1024x768 resolution

### Recommended Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB or more
- **Disk Space**: 5GB free space
- **Display**: 1920x1080 resolution

## Troubleshooting

### PaddleOCR not initializing
**Solution:**
- Ensure you have Microsoft Visual C++ Redistributable installed
  - Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
- Try using EasyOCR or AI OCR mode instead

### EasyOCR DLL errors
**Solution:**
- Install/Reinstall Microsoft Visual C++ Redistributable
- The application will fall back to AI OCR if configured

### Out of memory errors
**Solutions:**
- Process fewer pages at once
- Close other applications
- Use AI OCR mode (lower memory usage than local OCR)
- Increase system RAM if possible

### API key errors
**Solutions:**
- Verify your API key is correct
- Check if the API key has sufficient credits/quota
- Ensure internet connection is stable

### PDF conversion fails
**Solutions:**
- Ensure the PDF is not password-protected
- Try extracting images from PDF manually
- Some PDFs may have compatibility issues - try a different PDF

## Features

### Core Features
- ✅ PDF to Markdown conversion
- ✅ Image to Markdown conversion
- ✅ Local OCR (PaddleOCR, EasyOCR)
- ✅ AI-powered OCR (Vision models)
- ✅ Diagram detection
- ✅ Direct Obsidian vault integration

### Advanced Features (with API keys)
- ✅ AI text refinement
- ✅ Smart cross-referencing
- ✅ Metadata extraction
- ✅ Better text cleaning

## Building from Source

To build your own executable:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Install PyInstaller
pip install pyinstaller

# Run build script
build.bat

# Or manually:
pyinstaller build_exe.spec
```

The executable will be created in `dist\ObsidianNotesConverter.exe`

## Support

For issues, questions, or feature requests:
- Create an issue on GitHub
- Check existing issues for solutions
- Provide detailed error messages and logs

## License
MIT License - see LICENSE file for details
