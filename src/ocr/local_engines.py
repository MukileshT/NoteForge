"""Local OCR Engine Implementations"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from abc import ABC, abstractmethod



try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

from core.note_session import TextBlock
from ocr.preprocessing import ImagePreprocessor
from utils.logger import get_logger

logger = get_logger(__name__)

class LocalOCREngine(ABC):
    """Abstract base for local OCR engines"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
    
    @abstractmethod
    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text from image
        
        Returns:
            (full_text, text_blocks, confidence_score)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available"""
        pass

class TesseractEngine(LocalOCREngine):
    """Tesseract OCR for printed/clean text"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        super().__init__()
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def is_available(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except:
            return False
    
    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text using Tesseract"""
        # Preprocess image
        img = self.preprocessor.preprocess(image_path)
        
        # Get detailed OCR data
        ocr_data = pytesseract.image_to_data(
            img, output_type=pytesseract.Output.DICT, lang='eng'
        )
        
        # Extract full text
        full_text = pytesseract.image_to_string(img, lang='eng')
        
        # Build text blocks from OCR data
        text_blocks, avg_confidence = self._build_blocks(ocr_data, img.shape)
        
        logger.info(f"Tesseract: {len(text_blocks)} blocks, confidence={avg_confidence:.2f}")
        return full_text.strip(), text_blocks, avg_confidence
    
    def _build_blocks(self, ocr_data: Dict, img_shape: Tuple) -> Tuple[List[TextBlock], float]:
        """Build text blocks from OCR data"""
        h, w = img_shape[:2]
        blocks = []
        confidences = []
        
        current_line = []
        current_bbox = None
        current_confs = []
        
        for i in range(len(ocr_data['text'])):
            conf = int(ocr_data['conf'][i])
            text = ocr_data['text'][i].strip()
            
            # Skip low confidence or empty
            if conf < 30 or not text:
                continue
            
            # Normalize bbox
            x = ocr_data['left'][i] / w
            y = ocr_data['top'][i] / h
            bw = ocr_data['width'][i] / w
            bh = ocr_data['height'][i] / h
            
            # Check if same line (within 5px vertical distance)
            if current_bbox is None:
                current_bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current_line = [text]
                current_confs = [conf]
            elif abs(y - current_bbox['y']) < 0.01:  # Same line
                # Expand bbox
                right = max(current_bbox['x'] + current_bbox['width'], x + bw)
                current_bbox['width'] = right - current_bbox['x']
                current_bbox['height'] = max(current_bbox['height'], bh)
                current_line.append(text)
                current_confs.append(conf)
            else:  # New line
                # Save current block
                if current_line:
                    avg_conf = sum(current_confs) / len(current_confs) / 100.0
                    blocks.append(TextBlock(
                        content=' '.join(current_line),
                        bbox=current_bbox,
                        confidence=avg_conf
                    ))
                    confidences.append(avg_conf)
                
                # Start new block
                current_bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current_line = [text]
                current_confs = [conf]
        
        # Add last block
        if current_line:
            avg_conf = sum(current_confs) / len(current_confs) / 100.0
            blocks.append(TextBlock(
                content=' '.join(current_line),
                bbox=current_bbox,
                confidence=avg_conf
            ))
            confidences.append(avg_conf)
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return blocks, overall_confidence

class PaddleOCREngine(LocalOCREngine):
    """PaddleOCR for handwritten text"""
    _instance = None
    _initialized = False
    _available = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Ensure we initialize PaddleOCR only once per process
        if self._initialized:
            return
        super().__init__()
        self._ocr = None
        
        # Check paddle compatibility before initializing
        if not self._check_paddle_compatibility():
            logger.error("PaddleOCR initialization skipped due to compatibility issues")
            self._available = False
            self._initialized = True
            return
        
        try:
            from paddleocr import PaddleOCR
            # Use minimal parameters (use_gpu not supported in all versions)
            self._ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            self._available = True
            logger.info("PaddleOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self._ocr = None
            self._available = False
        finally:
            self._initialized = True
    
    def _check_paddle_compatibility(self) -> bool:
        """
        Check if paddle and paddleocr are compatible versions.
        
        Returns:
            True if compatible, False otherwise
        """
        try:
            import paddle
            paddle_version = paddle.__version__
            logger.info(f"Detected paddle {paddle_version}")
            
            # Check if inference API exists
            try:
                from paddle.inference import Config
                config = Config()
                
                # Check for the problematic method
                if not hasattr(config, 'set_optimization_level'):
                    logger.warning(
                        "paddle.inference.Config missing 'set_optimization_level' method. "
                        "This version incompatibility will cause PaddleOCR failures. "
                        "Fix: pip install --force-reinstall paddlepaddle==2.6.2"
                    )
                    return False
                
            except Exception as e:
                logger.warning(f"Could not verify paddle.inference API: {e}")
                # Continue anyway, might work
            
            # Now check paddleocr (may fail due to DLL issues)
            try:
                import paddleocr
                paddleocr_version = paddleocr.__version__
                logger.info(f"Detected paddleocr {paddleocr_version}")
            except Exception as e:
                logger.error(f"paddleocr import failed: {e}")
                logger.info("PaddleOCR unavailable, will use EasyOCR fallback")
                return False
            
            return True
            
        except ImportError as e:
            logger.error(f"paddle not installed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking paddle compatibility: {e}")
            return False

    def is_available(self) -> bool:
        return bool(self._available)
    
    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text using PaddleOCR"""
        if self._ocr is None:
            logger.error("PaddleOCR is not initialized.")
            raise RuntimeError("PaddleOCR unavailable")
        
        try:
            # PaddleOCR works on original image (it does its own preprocessing)
            result = self._ocr.ocr(str(image_path))
            
            if not result or not result[0]:
                return "", [], 0.0
            
            # Parse results
            full_text_parts = []
            text_blocks = []
            confidences = []
            
            # Get image dimensions for normalization
            img = cv2.imread(str(image_path))
            h, w = img.shape[:2]
            
            for line in result[0]:
                if not line:
                    continue
                
                bbox_coords = line[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                text_info = line[1]    # (text, confidence)
                
                text = text_info[0]
                conf = text_info[1]
                
                if conf < 0.3:  # Skip low confidence
                    continue
                
                # Normalize bbox to 0-1
                xs = [p[0] for p in bbox_coords]
                ys = [p[1] for p in bbox_coords]
                
                bbox = {
                    'x': min(xs) / w,
                    'y': min(ys) / h,
                    'width': (max(xs) - min(xs)) / w,
                    'height': (max(ys) - min(ys)) / h
                }
                
                text_blocks.append(TextBlock(
                    content=text,
                    bbox=bbox,
                    confidence=conf
                ))
                
                full_text_parts.append(text)
                confidences.append(conf)
            
            full_text = ' '.join(full_text_parts)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(f"PaddleOCR: {len(text_blocks)} blocks, confidence={avg_conf:.2f}")
            return full_text, text_blocks, avg_conf
        except Exception as e:
            logger.error(f"PaddleOCR failed: {e}")
            # Mark as permanently unavailable for this run
            self._available = False
            raise

class EasyOCREngine(LocalOCREngine):
    """EasyOCR as fallback with optional GPU support and CPU fallback"""

    def __init__(self, gpu: bool = False):
        super().__init__()
        self._reader = None
        self._available = None
        self._requested_gpu = bool(gpu)
        # Probe availability lazily but record failures
        try:
            self._available = True
        except Exception as e:
            logger.debug(f"EasyOCR import failed: {e}")
            self._available = False

    def is_available(self) -> bool:
        return bool(self._available)

    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text using EasyOCR. Attempts GPU init if requested, falls back to CPU on failure."""
        if not self._available:
            raise RuntimeError("EasyOCR unavailable")
        if self._reader is None:
            try:
                import easyocr
                # Attempt requested mode first
                try:
                    self._reader = easyocr.Reader(['en'], gpu=self._requested_gpu)
                except Exception as e:
                    logger.warning(f"EasyOCR reader init with gpu={self._requested_gpu} failed: {e}")
                    if self._requested_gpu:
                        # Attempt CPU fallback
                        try:
                            self._reader = easyocr.Reader(['en'], gpu=False)
                            logger.info("EasyOCR initialized with CPU fallback after GPU init failure")
                        except Exception as e2:
                            logger.error(f"EasyOCR CPU fallback also failed: {e2}")
                            self._available = False
                            raise
                    else:
                        logger.error(f"EasyOCR reader init failed: {e}")
                        self._available = False
                        raise
            except Exception as e:
                logger.error(f"Failed to initialize EasyOCR reader: {e}")
                self._available = False
                raise

        # Read image
        result = self._reader.readtext(str(image_path))
        
        # Get image dimensions
        img = cv2.imread(str(image_path))
        h, w = img.shape[:2]
        
        full_text_parts = []
        text_blocks = []
        confidences = []
        
        for detection in result:
            bbox_coords = detection[0]  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = detection[1]
            conf = detection[2]
            
            if conf < 0.3:
                continue
            
            # Normalize bbox
            xs = [p[0] for p in bbox_coords]
            ys = [p[1] for p in bbox_coords]
            
            bbox = {
                'x': min(xs) / w,
                'y': min(ys) / h,
                'width': (max(xs) - min(xs)) / w,
                'height': (max(ys) - min(ys)) / h
            }
            
            text_blocks.append(TextBlock(
                content=text,
                bbox=bbox,
                confidence=conf
            ))
            
            full_text_parts.append(text)
            confidences.append(conf)
        
        full_text = ' '.join(full_text_parts)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        
        logger.info(f"EasyOCR: {len(text_blocks)} blocks, confidence={avg_conf:.2f}")
        return full_text, text_blocks, avg_conf
