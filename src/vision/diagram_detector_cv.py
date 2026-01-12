"""OpenCV-based Diagram Detection"""
import cv2
import numpy as np
from pathlib import Path
from typing import List
from core.note_session import DiagramRegion
from utils.logger import get_logger

logger = get_logger(__name__)

class CVDiagramDetector:
    """Detect diagrams using OpenCV (no AI required)"""
    
    def __init__(self,
                 min_area_ratio: float = 0.02,
                 max_area_ratio: float = 0.8,
                 min_aspect_ratio: float = 0.3,
                 max_aspect_ratio: float = 3.0,
                 text_density_threshold: float = 0.1):
        """
        Args:
            min_area_ratio: Minimum diagram area as ratio of image
            max_area_ratio: Maximum diagram area as ratio of image
            min_aspect_ratio: Minimum width/height ratio
            max_aspect_ratio: Maximum width/height ratio
            text_density_threshold: Max text density to be considered diagram
        """
        self.min_area_ratio = min_area_ratio
        self.max_area_ratio = max_area_ratio
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.text_density_threshold = text_density_threshold
    
    def detect(self, image_path: Path) -> List[DiagramRegion]:
        """Detect diagrams in image
        
        Returns:
            List of DiagramRegion objects
        """
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Cannot load image: {image_path}")
            return []
        
        h, w = img.shape[:2]
        total_area = h * w
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate to connect components
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        
        for contour in contours:
            # Get bounding box
            x, y, cw, ch = cv2.boundingRect(contour)
            
            # Calculate metrics
            area = cw * ch
            area_ratio = area / total_area
            aspect_ratio = cw / ch if ch > 0 else 0
            
            # Filter by size
            if area_ratio < self.min_area_ratio or area_ratio > self.max_area_ratio:
                continue
            
            # Filter by aspect ratio
            if aspect_ratio < self.min_aspect_ratio or aspect_ratio > self.max_aspect_ratio:
                continue
            
            # Check text density in region
            roi = gray[y:y+ch, x:x+cw]
            text_density = self._estimate_text_density(roi)
            
            # Low text density = likely diagram
            if text_density <= self.text_density_threshold:
                # Classify diagram type
                diagram_type = self._classify_diagram_type(roi)
                
                # Normalize bbox
                bbox = {
                    'x': x / w,
                    'y': y / h,
                    'width': cw / w,
                    'height': ch / h
                }
                
                regions.append(DiagramRegion(
                    bbox=bbox,
                    diagram_type=diagram_type
                ))
                
                logger.debug(f"Detected {diagram_type}: area_ratio={area_ratio:.3f}, "
                           f"text_density={text_density:.3f}")
        
        logger.info(f"Detected {len(regions)} diagrams in {image_path.name}")
        return regions
    
    def _estimate_text_density(self, roi: np.ndarray) -> float:
        """Estimate text density in region (0-1)"""
        # Apply threshold
        _, thresh = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Count text pixels (assuming text is darker)
        text_pixels = np.sum(thresh > 0)
        total_pixels = roi.shape[0] * roi.shape[1]
        
        return text_pixels / total_pixels if total_pixels > 0 else 0
    
    def _classify_diagram_type(self, roi: np.ndarray) -> str:
        """Classify type of diagram based on visual features"""
        # Detect lines
        edges = cv2.Canny(roi, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 50, minLineLength=30, maxLineGap=10)
        
        if lines is None:
            return "diagram"
        
        num_lines = len(lines)
        
        # Analyze line angles
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            angles.append(abs(angle))
        
        # Check for horizontal/vertical lines (circuit/diagram)
        horiz_vert_lines = sum(1 for a in angles if a < 15 or a > 165 or 75 < a < 105)
        
        if horiz_vert_lines / num_lines > 0.6:
            # Detect circles (might be circuit symbols)
            circles = cv2.HoughCircles(
                roi, cv2.HOUGH_GRADIENT, 1, 20,
                param1=50, param2=30, minRadius=5, maxRadius=50
            )
            
            if circles is not None and len(circles[0]) > 2:
                return "circuit"
            else:
                return "diagram"
        
        # Check for table structure (many horizontal/vertical lines)
        if num_lines > 10 and horiz_vert_lines / num_lines > 0.8:
            return "table"
        
        # Check for curves (might be graph)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        curved_contours = sum(1 for c in contours if cv2.arcLength(c, False) > 100)
        
        if curved_contours > 0:
            return "graph"
        
        return "diagram"
    
    def detect_with_ai_fallback(self, image_path: Path, 
                                llm_provider=None) -> List[DiagramRegion]:
        """Detect diagrams, fallback to AI if needed"""
        # Try OpenCV first
        regions = self.detect(image_path)
        
        # If no diagrams found and AI is available, try AI
        if not regions and llm_provider and llm_provider.supports_vision():
            logger.info(f"No diagrams found with CV, trying AI for {image_path.name}")
            return self._detect_with_ai(image_path, llm_provider)
        
        return regions
    
    def _detect_with_ai(self, image_path: Path, llm_provider) -> List[DiagramRegion]:
        """Detect diagrams using AI vision"""
        prompt = """Detect all diagrams, graphs, circuits, tables, or drawings in this image.
Return ONLY JSON array:
[
    {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "type": "circuit"},
    ...
]
Coordinates normalized 0-1. type: diagram, graph, circuit, table"""
        
        try:
            response = llm_provider.complete_with_image(prompt, image_path)
            
            # Parse JSON
            import json
            import re
            
            content = response.content.strip()
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                else:
                    return []
            
            data = json.loads(json_str)
            
            regions = []
            for item in data:
                if 'x' in item and 'y' in item:
                    bbox = {
                        'x': item['x'],
                        'y': item['y'],
                        'width': item.get('width', 0.1),
                        'height': item.get('height', 0.1)
                    }
                    regions.append(DiagramRegion(
                        bbox=bbox,
                        diagram_type=item.get('type', 'diagram')
                    ))
            
            logger.info(f"AI detected {len(regions)} diagrams")
            return regions
        
        except Exception as e:
            logger.error(f"AI diagram detection failed: {e}")
            return []
