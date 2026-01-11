from pathlib import Path
from typing import Dict, List
from core.note_session import TextBlock
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class OCREngine:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
    
    def process_page(self, image_path: Path) -> Dict:
        ocr_prompt = """Extract all visible text from this image. Provide the full extracted text and a list of detected text blocks. Each text block should include its content, and its bounding box (x, y, width, height) normalized from 0 to 1. Organize the text blocks by their approximate reading order (top to bottom, then left to right).

Return ONLY JSON:
```json
{
  "full_text": "...",
  "text_blocks": [
    {"content": "...", "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}},
    {"content": "...", "bbox": {"x": 0.1, "y": 0.3, "width": 0.4, "height": 0.05}},
    ...
  ]
}
```
"""
        try:
            ai_response = self.ai_client.analyze_image(image_path, ocr_prompt)
            
            full_text = ai_response.get("full_text", "")
            ai_text_blocks = ai_response.get("text_blocks", [])

            text_blocks = []
            for block_data in ai_text_blocks:
                content = block_data.get("content", "")
                bbox = block_data.get("bbox", {})
                if content and bbox:
                    text_blocks.append(TextBlock(content=content, bbox=bbox))
            
            logger.info(f"OCR Full Text for {image_path.name}:\n{full_text.strip()}")
            return {'text_blocks': text_blocks, 'full_text': full_text.strip()}
        except Exception as e:
            logger.error(f"An unexpected error occurred during AI OCR: {e}", exc_info=True)
            raise
