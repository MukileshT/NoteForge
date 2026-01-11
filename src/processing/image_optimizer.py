from pathlib import Path
from PIL import Image
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageOptimizer:
    def __init__(self, config):
        self.config = config
        self.max_w = config.get('image_optimization.max_diagram_width', 1200)
        self.max_h = config.get('image_optimization.max_diagram_height', 1200)
        self.quality = config.get('image_optimization.diagram_quality', 85)
    
    def optimize_session_images(self, session: NoteSession, vault_path: Path):
        assets_dir = vault_path / self.config.get('vault.assets_folder') / session.assets_folder
        assets_dir.mkdir(parents=True, exist_ok=True)
        for page in session.pages:
            for diagram in page.diagram_regions:
                if diagram.label:
                    optimized = self._optimize_diagram(page.raw_image_path, diagram.bbox, assets_dir, diagram.label)
                    diagram.image_path = optimized
    
    def _optimize_diagram(self, source: Path, bbox: dict, output_dir: Path, label: str) -> Path:
        img = Image.open(source)
        w, h = img.size
        x1 = int(bbox['x'] * w)
        y1 = int(bbox['y'] * h)
        x2 = int((bbox['x'] + bbox['width']) * w)
        y2 = int((bbox['y'] + bbox['height']) * h)
        cropped = img.crop((x1, y1, x2, y2))
        if cropped.width > self.max_w or cropped.height > self.max_h:
            cropped.thumbnail((self.max_w, self.max_h), Image.LANCZOS)
        filename = f"{label.replace('.', '_')}.png"
        output_path = output_dir / filename
        cropped.save(output_path, "PNG", optimize=True, quality=self.quality)
        return output_path
