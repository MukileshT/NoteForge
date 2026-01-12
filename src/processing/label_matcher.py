from typing import Dict
import re
from core.note_session import NoteSession, DiagramRegion
from utils.validators import extract_label_info
from utils.geometry import BoundingBox, calculate_nearest_box
from utils.logger import get_logger

logger = get_logger(__name__)

class LabelMatcher:
    def __init__(self, config):
        self.config = config
        self.label_pattern = config.get('label_matching.label_pattern')
        self.max_distance_mult = config.get('label_matching.max_distance_multiplier', 1.5)
        self.direction_priority = config.get('label_matching.direction_priority')
    
    def match_labels(self, session: NoteSession):
        for page in session.pages:
            self._match_page(page, session)
    
    def _match_page(self, page, session):
        labels = self._find_labels(page.text_blocks)
        diagrams = page.diagram_regions
        if not labels or not diagrams:
            return
        label_counts = {}
        for label_text, label_bbox in labels:
            info = extract_label_info(label_text)
            if not info:
                continue
            label_box = BoundingBox(label_bbox['x'], label_bbox['y'], label_bbox['width'], label_bbox['height'])
            diagram_boxes = [BoundingBox(d.bbox['x'], d.bbox['y'], d.bbox['width'], d.bbox['height']) for d in diagrams]
            max_dist = label_box.height * self.max_distance_mult
            idx, nearest, dist = calculate_nearest_box(label_box, diagram_boxes, max_dist, self.direction_priority)
            if idx is not None:
                base_label = info['full']
                if base_label in label_counts:
                    label_counts[base_label] += 1
                    final_label = f"{base_label}{chr(96 + label_counts[base_label])}"
                    session.add_warning(f"Duplicate label {base_label}, renamed to {final_label}")
                else:
                    label_counts[base_label] = 0
                    final_label = base_label
                diagrams[idx].label = final_label
    
    def _find_labels(self, text_blocks) -> list:
        labels = []
        for block in text_blocks:
            matches = re.finditer(self.label_pattern, block.content, re.IGNORECASE)
            for match in matches:
                labels.append((match.group(0), block.bbox))
        return labels
