from pathlib import Path
from PIL import Image
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageOptimizer:
    def __init__(self, config):
        self.config = config
        # Use central config keys `image.max_width` and `image.quality`
        self.max_w = int(self.config.get('image.max_width', 1200))
        self.quality = int(self.config.get('image.quality', 70))
    
    def optimize_session_images(self, session: NoteSession, vault_path: Path):
        assets_dir = vault_path / self.config.get('vault.assets_folder', 'assets')
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Track figure numbering across all pages
        figure_counter = {}  # {page_number: {figure_number: count}}
        
        for page in session.pages:
            page_num = page.page_number
            if page_num not in figure_counter:
                figure_counter[page_num] = {}
            
            for idx, diagram in enumerate(page.diagram_regions):
                # Generate label if not present
                if not diagram.label:
                    # Use page number and index: fig{page}.{idx+1}
                    diagram.label = f"fig{page_num}.{idx+1}"
                    logger.info(f"Generated label {diagram.label} for diagram on page {page_num}")
                
                # Crop and save diagram
                optimized = self._optimize_diagram(
                    page.raw_image_path,
                    diagram.bbox,
                    assets_dir,
                    diagram.label,
                    session.filename_base
                )
                diagram.image_path = optimized
                
                # Generate caption if not present
                if not diagram.caption:
                    diagram.caption = self._format_caption(diagram.label)
    
    def _optimize_diagram(self, source: Path, bbox: dict, output_dir: Path, label: str, session_filename_base: str) -> Path:
        img = Image.open(source)
        w, h = img.size
        x1 = int(bbox['x'] * w)
        y1 = int(bbox['y'] * h)
        x2 = int((bbox['x'] + bbox['width']) * w)
        y2 = int((bbox['y'] + bbox['height']) * h)
        cropped = img.crop((x1, y1, x2, y2))

        # Ensure we never store raw camera-resolution images: resize to max width
        if cropped.width > self.max_w:
            ratio = self.max_w / float(cropped.width)
            new_h = int(cropped.height * ratio)
            cropped = cropped.resize((self.max_w, new_h), Image.LANCZOS)

        # Strip metadata by creating a new image without info
        data = list(cropped.getdata())
        clean = Image.new(cropped.mode, cropped.size)
        clean.putdata(data)

        # Choose PNG for diagrams to preserve clarity but ensure optimization
        safe_label = label.replace('.', '_')
        filename = f"fig{safe_label}.png"
        output_path = output_dir / filename

        try:
            # Save without metadata and with optimization
            clean.save(output_path, format='PNG', optimize=True)
        except Exception:
            # Fallback to JPEG with quality settings if PNG save fails
            jpg_name = f"fig{safe_label}.jpg"
            output_path = output_dir / jpg_name
            rgb = clean.convert('RGB')
            rgb.save(output_path, format='JPEG', quality=self.quality, optimize=True)

        logger.info(f"Saved diagram {label} to {output_path.name}")
        return output_path
    
    def _format_caption(self, label: str) -> str:
        """Format caption from label (e.g., fig1.2 -> Figure 1.2)"""
        import re
        label_lower = label.lower()
        if label_lower.startswith('fig'):
            kind = 'Figure'
        elif label_lower.startswith('gr'):
            kind = 'Graph'
        elif label_lower.startswith('tbl'):
            kind = 'Table'
        else:
            kind = 'Diagram'
        
        # Extract numbers
        numbers = re.findall(r'\d+', label)
        if len(numbers) >= 2:
            return f"{kind} {numbers[0]}.{numbers[1]}"
        elif len(numbers) == 1:
            return f"{kind} {numbers[0]}"
        else:
            return label
