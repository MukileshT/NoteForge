from pathlib import Path
from typing import List
from core.note_session import DiagramRegion
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class DiagramDetector:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
    
    def detect(self, image_path: Path) -> List[DiagramRegion]:
        prompt = '''Detect all diagrams, graphs, circuits, or drawings in this image.
Return ONLY JSON array:
[
    {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "type": "circuit"},
    ...
]
Coordinates are normalized 0-1. type: diagram, graph, circuit, table'''
        try:
            result = self.ai_client.analyze_image(image_path, prompt)
            if isinstance(result, list):
                regions = []
                for r in result:
                    regions.append(DiagramRegion(
                        bbox={'x': r['x'], 'y': r['y'], 'width': r['width'], 'height': r['height']},
                        diagram_type=r.get('type', 'diagram')
                    ))
                return regions
            logger.warning(f"AI client returned non-list result for diagram detection: {type(result)}")
            return []
        except Exception as e:
            logger.error(f"Failed to detect diagrams using AI client: {e}", exc_info=True)
            raise
