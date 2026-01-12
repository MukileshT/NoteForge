"""Local OCR Engine Implementations"""
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from abc import ABC, abstractmethod
from datetime import datetime
import json

# #region agent log
try:
    with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_before_cv2", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:10", "message": "Before importing cv2", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
except: pass
# #endregion

try:
    import cv2
    import numpy as np
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_cv2_success", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:15", "message": "Successfully imported cv2 and numpy", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
    except: pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_cv2_error", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:19", "message": "ImportError: cv2/numpy missing", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
    except: pass
    # #endregion
    cv2 = None
    np = None

# #region agent log
try:
    with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_before_tesseract", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:25", "message": "Before importing pytesseract", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}) + "\n")
except: pass
# #endregion

try:
    import pytesseract
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_tesseract_success", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:29", "message": "Successfully imported pytesseract", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}) + "\n")
    except: pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_ocr_tesseract_error", "timestamp": int(datetime.now().timestamp() * 1000), "location": "local_engines.py:33", "message": "ImportError: pytesseract missing", "data": {"error_type": type(e).__name__, "error_msg": str(e)}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}) + "\n")
    except: pass
    # #endregion
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
    
    def __init__(self):
        super().__init__()
        self._ocr = None
    
    def is_available(self) -> bool:
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False
    
    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text using PaddleOCR"""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        
        # PaddleOCR works on original image (it does its own preprocessing)
        result = self._ocr.ocr(str(image_path), cls=True)
        
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

class EasyOCREngine(LocalOCREngine):
    """EasyOCR as fallback"""
    
    def __init__(self):
        super().__init__()
        self._reader = None
    
    def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False
    
    def extract_text(self, image_path: Path) -> Tuple[str, List[TextBlock], float]:
        """Extract text using EasyOCR"""
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(['en'], gpu=False)
        
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
