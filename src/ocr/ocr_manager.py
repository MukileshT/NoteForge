"""Unified OCR Manager with Local and AI modes"""
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

from core.note_session import TextBlock, DiagramRegion
from ocr.local_engines import PaddleOCREngine, EasyOCREngine
from ocr.preprocessing import ImagePreprocessor
from utils.logger import get_logger

logger = get_logger(__name__)

class OCRMode(Enum):
    """OCR operation modes"""
    LOCAL = "local"  # Default: PaddleOCR + EasyOCR
    AI = "ai"        # AI-powered OCR (vision models)

class OCRManager:
    """Manages OCR operations with multiple engines"""
    
    def __init__(self, mode: OCRMode = OCRMode.LOCAL, 
                 tesseract_path: Optional[str] = None,
                 confidence_threshold: float = 0.6,
                 llm_provider=None,
                 easyocr_gpu: bool = False):
        """
        Args:
            mode: OCR mode (LOCAL or AI)
            tesseract_path: Path to tesseract executable (deprecated, uses PaddleOCR by default)
            confidence_threshold: Minimum confidence to accept OCR results
            llm_provider: LLM provider for AI mode
        """
        self.mode = mode
        self.confidence_threshold = confidence_threshold
        self.llm_provider = llm_provider
        # Initialize preprocessor
        self.preprocessor = ImagePreprocessor()
        # Read ai fallback setting from raw config to avoid circular imports
        try:
            import json
            cfg_path = Path('config') / 'app_config.json'
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    self.use_ai_fallback = cfg.get('ocr', {}).get('use_ai_fallback', True)
            else:
                self.use_ai_fallback = True
        except Exception:
            self.use_ai_fallback = True
        
        # Initialize local engines (pass GPU preference to EasyOCR)
        self.paddle = PaddleOCREngine()
        try:
            self.easyocr = EasyOCREngine(gpu=bool(easyocr_gpu))
        except TypeError:
            # Older EasyOCREngine signature may not accept gpu arg; fallback
            self.easyocr = EasyOCREngine()
        
        # Check availability
        self.local_engines_available = {
            'paddleocr': self.paddle.is_available(),
            'easyocr': self.easyocr.is_available()
        }
        
        logger.info(f"OCR Manager initialized in {mode.value} mode")
        logger.info(f"Available engines: {[k for k, v in self.local_engines_available.items() if v]}")
    
    def extract_text(self, image_path: Path, 
                     is_handwritten: bool = False) -> Dict:
        """Extract text from image
        
        Args:
            image_path: Path to image
            is_handwritten: True if image contains handwritten text
        
        Returns:
            Dict with 'full_text', 'text_blocks', 'confidence'
        """
        if self.mode == OCRMode.AI:
            return self._extract_text_ai(image_path)
        else:
            return self._extract_text_local(image_path, is_handwritten)
    
    def _extract_text_local(self, image_path: Path, 
                           is_handwritten: bool) -> Dict:
        """Extract text using local engines"""
        
        # Prioritize local OCR engines
        if self.local_engines_available.get('paddleocr'):
            try:
                logger.info(f"Using PaddleOCR for text extraction: {image_path.name}")
                full_text, blocks, conf = self.paddle.extract_text(image_path)

                if conf >= self.confidence_threshold:
                    return {
                        'full_text': full_text,
                        'text_blocks': blocks,
                        'confidence': conf,
                        'engine': 'paddleocr'
                    }
            except Exception as e:
                logger.error(f"PaddleOCR failed: {e}")
                # Mark paddle as unavailable for remainder of run
                self.local_engines_available['paddleocr'] = False

        if self.local_engines_available.get('easyocr'):
            try:
                logger.info(f"Using EasyOCR for text extraction: {image_path.name}")
                full_text, blocks, conf = self.easyocr.extract_text(image_path)
                return {
                    'full_text': full_text,
                    'text_blocks': blocks,
                    'confidence': conf,
                    'engine': 'easyocr'
                }
            except Exception as e:
                logger.error(f"EasyOCR failed: {e}")
                # Mark easyocr as unavailable for remainder of run
                self.local_engines_available['easyocr'] = False

        # If local OCR failed, decide on AI fallback based on config
        if self.use_ai_fallback:
            logger.info("Local OCR failed; AI fallback enabled — invoking AI once")
            return self._extract_text_ai(image_path)

        # No AI fallback -> fail fast
        raise RuntimeError("All local OCR engines failed and AI fallback is disabled")
    
    def _extract_text_ai(self, image_path: Path) -> Dict:
        """Extract text using AI vision models"""
        if not self.llm_provider:
            raise RuntimeError("LLM provider not configured for AI OCR")
        
        if not self.llm_provider.supports_vision():
            raise RuntimeError(f"Provider {self.llm_provider.config.provider} does not support vision")
        
        prompt = """Extract all visible text from this image. Provide:
1. Full extracted text
2. List of text blocks with bounding boxes (x, y, width, height normalized 0-1)

Return ONLY JSON:
{
  "full_text": "...",
  "text_blocks": [
    {"content": "...", "bbox": {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.05}}
  ]
}"""
        
        try:
            response = self.llm_provider.complete_with_image(prompt, image_path)
            
            # Parse JSON response
            import json
            import re
            
            content = response.content.strip()
            
            # Extract JSON from markdown code blocks if present
            match = re.search(r'```(?:json)?\s*({.*?})\s*```', content, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # Try to find JSON directly
                match = re.search(r'{.*}', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    raise ValueError("No JSON found in AI response")
            
            data = json.loads(json_str)
            
            full_text = data.get('full_text', '')
            blocks_data = data.get('text_blocks', [])
            
            text_blocks = [
                TextBlock(
                    content=b.get('content', ''),
                    bbox=b.get('bbox', {}),
                    confidence=1.0  # AI models don't provide confidence scores
                )
                for b in blocks_data
                if b.get('content') and b.get('bbox')
            ]
            
            logger.info(f"AI OCR: {len(text_blocks)} blocks extracted")
            
            return {
                'full_text': full_text,
                'text_blocks': text_blocks,
                'confidence': 1.0,  # Assume high confidence for AI
                'engine': 'ai',
                'tokens_used': response.tokens_used
            }
        
        except Exception as e:
            logger.error(f"AI OCR failed: {e}")
            raise
    
    def set_mode(self, mode: OCRMode):
        """Change OCR mode"""
        self.mode = mode
        logger.info(f"OCR mode changed to: {mode.value}")
