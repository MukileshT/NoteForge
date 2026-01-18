# Obsidian Notes Converter

Convert handwritten notes (PDF/images) to Obsidian Markdown with AI-powered OCR.

## Quick Setup

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up PaddleOCR (for local OCR)
python scripts/setup_paddleocr.py

# 4. Run the application
python main.py
```

## Configuration

### Application Settings
This project uses `config/app_config.json` as the single source of truth:

- **Models**: `models.selected` and `models.available` control which LLM is used
- **Image settings**: `image.max_width` and `image.quality` control resizing/compression
- **OCR**: `ocr.mode` and `ocr.confidence_threshold` control OCR behavior

### API Keys
API keys are stored encrypted under `%APPDATA%/YourApp/keys.enc` (Windows).
Use "Manage API Keys" in the GUI to add keys.

### Environment Variables (Optional)
Copy `.env.example` to `.env` and customize:

```bash
# Custom PaddleOCR installation path (optional)
PADDLEOCR_HOME=

# OCR mode: local, ai, or disabled
OCR_MODE=local
```

## OCR Modes

- **local**: Uses PaddleOCR (handwritten) or EasyOCR (printed) - no API calls
- **ai**: Uses AI vision models (OpenAI, Anthropic, Gemini)
- **disabled**: Skip OCR entirely

The application automatically falls back to EasyOCR if PaddleOCR is unavailable.

## Troubleshooting

### PaddleOCR Issues
If you see `'AnalysisConfig' object has no attribute 'set_optimization_level'`:

```bash
pip install --force-reinstall paddlepaddle==2.6.2
```

Or let the application use EasyOCR as fallback (automatic).

### Custom Models
To add a custom LLM: open the GUI, choose a provider, select "Other / Custom" in the Model dropdown, enter the model name and type, then click "Save Custom".
