import math
from typing import Tuple, List

class BoundingBox:
    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def top(self) -> float:
        return self.y
    
    @property
    def bottom(self) -> float:
        return self.y + self.height
    
    @property
    def left(self) -> float:
        return self.x
    
    @property
    def right(self) -> float:
        return self.x + self.width
    
    def distance_to(self, other: 'BoundingBox') -> float:
        x1, y1 = self.center
        x2, y2 = other.center
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    def direction_to(self, other: 'BoundingBox') -> str:
        x1, y1 = self.center
        x2, y2 = other.center
        dx = x2 - x1
        dy = y2 - y1
        if abs(dy) > abs(dx):
            return 'below' if dy > 0 else 'above'
        else:
            return 'right' if dx > 0 else 'left'
    
    def __repr__(self):
        return f"BoundingBox(x={self.x}, y={self.y}, w={self.width}, h={self.height})"

def calculate_nearest_box(target: BoundingBox, candidates: List[BoundingBox], 
                         max_distance: float = None, 
                         preferred_directions: List[str] = None) -> Tuple:
    if not candidates:
        return None, None, float('inf')
    if preferred_directions is None:
        preferred_directions = ['above', 'below', 'left', 'right']
    best_idx = None
    best_box = None
    best_distance = float('inf')
    for idx, candidate in enumerate(candidates):
        distance = target.distance_to(candidate)
        if max_distance and distance > max_distance:
            continue
        direction = target.direction_to(candidate)
        direction_score = preferred_directions.index(direction) if direction in preferred_directions else 999
        score = (direction_score * 10000) + distance
        if best_idx is None or score < (preferred_directions.index(target.direction_to(best_box)) * 10000 + best_distance):
            best_idx = idx
            best_box = candidate
            best_distance = distance
    return best_idx, best_box, best_distance
