# Obsidian Notes Converter

Convert handwritten notes (PDF/images) to Obsidian Markdown.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python main.py
```

## Configuration
This project uses a single source of truth config file at `config/app_config.json`.

- Models: `models.selected` and `models.available` control which model is used.
- Image settings: `image.max_width` and `image.quality` control resizing/compression.
- OCR: `ocr.mode` and `ocr.confidence_threshold` control OCR behavior.

API keys are stored encrypted under `%APPDATA%/YourApp/keys.enc` on Windows. Use "Manage API Keys" in the GUI to add keys.

To add a custom model: open the GUI, choose a provider, select "Other / Custom" in the Model dropdown, enter the model name and type, then click "Save Custom". The model will be added to `config/app_config.json` and set as selected.
