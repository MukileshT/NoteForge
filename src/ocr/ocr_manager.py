"""Unified OCR Manager with Local and AI modes"""
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from enum import Enum

from core.note_session import TextBlock, DiagramRegion
from ocr.local_engines import TesseractEngine, PaddleOCREngine, EasyOCREngine
from ocr.preprocessing import ImagePreprocessor
from utils.logger import get_logger

logger = get_logger(__name__)

class OCRMode(Enum):
    """OCR operation modes"""
    LOCAL = "local"  # Default: Tesseract + PaddleOCR + EasyOCR
    AI = "ai"        # AI-powered OCR (vision models)

class OCRManager:
    """Manages OCR operations with multiple engines"""
    
    def __init__(self, mode: OCRMode = OCRMode.LOCAL, 
                 tesseract_path: Optional[str] = None,
                 confidence_threshold: float = 0.6,
                 llm_provider=None):
        """
        Args:
            mode: OCR mode (LOCAL or AI)
            tesseract_path: Path to tesseract executable
            confidence_threshold: Minimum confidence to accept OCR results
            llm_provider: LLM provider for AI mode
        """
        self.mode = mode
        self.confidence_threshold = confidence_threshold
        self.llm_provider = llm_provider
        self.preprocessor = ImagePreprocessor()
        
        # Initialize local engines
        self.tesseract = TesseractEngine(tesseract_path)
        self.paddle = PaddleOCREngine()
        self.easyocr = EasyOCREngine()
        
        # Check availability
        self.local_engines_available = {
            'tesseract': self.tesseract.is_available(),
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
        
        if is_handwritten:
            # Try PaddleOCR first for handwritten
            if self.local_engines_available.get('paddleocr'):
                logger.info(f"Using PaddleOCR for handwritten text: {image_path.name}")
                full_text, blocks, conf = self.paddle.extract_text(image_path)
                
                if conf >= self.confidence_threshold:
                    return {
                        'full_text': full_text,
                        'text_blocks': blocks,
                        'confidence': conf,
                        'engine': 'paddleocr'
                    }
            
            # Fallback to EasyOCR
            if self.local_engines_available.get('easyocr'):
                logger.info(f"Falling back to EasyOCR: {image_path.name}")
                full_text, blocks, conf = self.easyocr.extract_text(image_path)
                return {
                    'full_text': full_text,
                    'text_blocks': blocks,
                    'confidence': conf,
                    'engine': 'easyocr'
                }
        
        # For printed text or fallback, use Tesseract
        if self.local_engines_available.get('tesseract'):
            logger.info(f"Using Tesseract for printed text: {image_path.name}")
            full_text, blocks, conf = self.tesseract.extract_text(image_path)
            
            if conf >= self.confidence_threshold:
                return {
                    'full_text': full_text,
                    'text_blocks': blocks,
                    'confidence': conf,
                    'engine': 'tesseract'
                }
            
            # If confidence is low, try cropped regions
            logger.warning(f"Low confidence ({conf:.2f}), retrying with cropped regions")
            return self._retry_with_crops(image_path)
        
        raise RuntimeError("No OCR engines available")
    
    def _retry_with_crops(self, image_path: Path) -> Dict:
        """Retry OCR on cropped text regions"""
        import cv2
        import tempfile
        import time
        
        # Create unique temp directory for this page to avoid collisions
        temp_dir = Path(tempfile.mkdtemp(prefix='ocr_page_'))
        
        try:
            # Detect text regions
            img = cv2.imread(str(image_path))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Use MSER to detect text regions
            mser = cv2.MSER_create()
            regions, _ = mser.detectRegions(gray)
            
            all_blocks = []
            full_text_parts = []
            
            h, w = img.shape[:2]
            
            for idx, region in enumerate(regions):
                # Get bounding box
                x, y, rw, rh = cv2.boundingRect(region.reshape(-1, 1, 2))
                
                # Skip tiny regions
                if rw < 20 or rh < 10:
                    continue
                
                # Crop and OCR - use unique filename per crop
                crop = img[y:y+rh, x:x+rw]
                
                # Create temp file but close it immediately before Tesseract uses it
                with tempfile.NamedTemporaryFile(
                    suffix='.png',
                    delete=False,
                    dir=temp_dir,
                    prefix=f'crop_{idx}_'
                ) as tmp:
                    tmp_path = Path(tmp.name)
                # File is now closed, safe for Tesseract to use
                
                try:
                    cv2.imwrite(str(tmp_path), crop)
                    text, _, conf = self.tesseract.extract_text(tmp_path)
                    if conf >= 0.5 and text.strip():
                        # Create text block
                        bbox = {
                            'x': x / w,
                            'y': y / h,
                            'width': rw / w,
                            'height': rh / h
                        }
                        all_blocks.append(TextBlock(
                            content=text.strip(),
                            bbox=bbox,
                            confidence=conf
                        ))
                        full_text_parts.append(text.strip())
                finally:
                    # Retry delete with small delay for Windows file locks
                    for attempt in range(3):
                        try:
                            tmp_path.unlink(missing_ok=True)
                            break
                        except PermissionError:
                            if attempt < 2:
                                time.sleep(0.1)
        finally:
            # Clean up temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        # Sort blocks by position (top to bottom, left to right)
        all_blocks.sort(key=lambda b: (b.bbox['y'], b.bbox['x']))
        
        avg_conf = sum(b.confidence for b in all_blocks) / len(all_blocks) if all_blocks else 0.0
        
        return {
            'full_text': ' '.join(full_text_parts),
            'text_blocks': all_blocks,
            'confidence': avg_conf,
            'engine': 'tesseract_cropped'
        }
    
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
