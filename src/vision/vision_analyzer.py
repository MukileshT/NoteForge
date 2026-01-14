from pathlib import Path
from typing import Dict, List, Any
import pytesseract
from PIL import Image
import cv2
import numpy as np
from core.note_session import TextBlock, DiagramRegion
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class VisionAnalyzer:
    def __init__(self, config):
        self.config = config
        # Lazy AI client creation to avoid requiring AI config for local-only runs
        self.ai_client = None
        # Read settings from ConfigManager (supports dotted keys)
        try:
            self.ocr_strategy = config.get('ocr.mode', config.get('ocr_strategy', 'ai'))
        except Exception:
            self.ocr_strategy = 'ai'
        try:
            self.tesseract_path = config.get('ocr.tesseract_path', config.get('tesseract_path'))
        except Exception:
            self.tesseract_path = None
        try:
            self.use_ai_fallback = config.get('ocr.use_ai_fallback', True)
        except Exception:
            self.use_ai_fallback = True

        if self.ocr_strategy == 'local':
            if self.tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            else:
                logger.warning("Local OCR strategy selected but tesseract_path not configured.")
                if self.use_ai_fallback:
                    logger.warning("Falling back to AI OCR.")
                    self.ocr_strategy = 'ai'
                else:
                    logger.error("Local OCR strategy failed and AI fallback is disabled.")
                    raise RuntimeError("OCR configuration error: Local OCR unavailable and AI fallback disabled.")

    def analyze_page(self, image_path: Path) -> Dict:
        if self.ocr_strategy == 'local':
            return self._analyze_page_local(image_path)
        else:
            return self._analyze_page_ai(image_path)

    def _analyze_page_ai(self, image_path: Path) -> Dict:
        # AI Call 1: Text Extraction (OCR)
        ocr_prompt = """Extract all visible text from this image. Provide the full extracted text and a list of detected text blocks. Each text block should include its content, and its bounding box (x, y, width, height) normalized from 0 to 1. Organize the text blocks by their approximate reading order (top to bottom, then left to right).

Return ONLY a single JSON object with the following structure:
```json
{
  "full_text": "...",
  "text_blocks": [
    {"content": "...", "bbox": {"x": ..., "y": ..., "width": ..., "height": ...}}
  ]
}
```
"""
        # AI Call 2: Diagram Detection
        diagram_prompt = """Detect all diagrams, graphs, circuits, or drawings in this image.
Return ONLY JSON array:
[
    {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "type": "circuit"},
    ...
]
Coordinates are normalized 0-1. type: diagram, graph, circuit, table"""
        try:
            # First AI call for Text Blocks
            if self.ai_client is None:
                self.ai_client = AIClient(self.config)
            text_ai_response = self.ai_client.analyze_image(image_path, ocr_prompt)
            full_text = text_ai_response.get("full_text", "")
            text_blocks_data = text_ai_response.get("text_blocks", [])
            text_blocks = [TextBlock(content=b.get("content", ""), bbox=b.get("bbox", {})) for b in text_blocks_data if b.get("content") and b.get("bbox")]
            
            # Second AI call for Diagram Regions
            diagram_ai_response = self.ai_client.analyze_image(image_path, diagram_prompt)
            # Ensure diagram_ai_response is a list, as expected by the prompt
            if not isinstance(diagram_ai_response, list):
                logger.warning(f"Diagram AI response for {image_path.name} was not a list. Received: {diagram_ai_response}. Attempting to parse as list.")
                diagram_regions_data = [] # Fallback to empty list
            else:
                diagram_regions_data = diagram_ai_response

            diagram_regions = [DiagramRegion(bbox=d.get("bbox", {}), diagram_type=d.get("type", "diagram")) for d in diagram_regions_data if d.get("bbox")]
            
            logger.info(f"Analyzed page {image_path.name} using AI, found {len(text_blocks)} text blocks and {len(diagram_regions)} diagrams.")

            return {
                'full_text': full_text,
                'text_blocks': text_blocks,
                'diagram_regions': diagram_regions
            }

        except Exception as e:
            logger.error(f"An unexpected error occurred during AI page analysis: {e}", exc_info=True)
            raise

    def _analyze_page_local(self, image_path: Path) -> Dict:
        try:
            img = Image.open(image_path)
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img = self._preprocess(cv_img)
            
            ocr_data = pytesseract.image_to_data(cv_img, output_type=pytesseract.Output.DICT)
            text_blocks = self._extract_blocks(ocr_data, img.size)
            full_text = pytesseract.image_to_string(cv_img)

            logger.info(f"Analyzed page {image_path.name} using local OCR, found {len(text_blocks)} text blocks.")
            
            # Local OCR does not detect diagrams automatically, so diagram_regions will be empty
            return {'full_text': full_text.strip(), 'text_blocks': text_blocks, 'diagram_regions': []}
        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found. Please install Tesseract OCR and ensure it's in your PATH, or switch to 'ai' ocr_strategy.")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during local page analysis: {e}", exc_info=True)
            raise

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    def _extract_blocks(self, ocr_data: Dict, img_size: tuple) -> List[TextBlock]:
        blocks = []
        w, h = img_size
        current = []
        bbox = None
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) < 30: # Filter low confidence
                continue
            text = ocr_data['text'][i].strip()
            if not text:
                continue
            x = ocr_data['left'][i] / w
            y = ocr_data['top'][i] / h
            bw = ocr_data['width'][i] / w
            bh = ocr_data['height'][i] / h
            if bbox is None:
                bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current = [text]
            elif abs(y - bbox['y']) < 0.005: # Adjusted threshold from before
                right = max(bbox['x'] + bbox['width'], x + bw)
                bbox['width'] = right - bbox['x']
                current.append(text)
            else:
                if current:
                    blocks.append(TextBlock(content=' '.join(current), bbox=bbox))
                bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current = [text]
        if current:
            blocks.append(TextBlock(content=' '.join(current), bbox=bbox))
        return blocks

