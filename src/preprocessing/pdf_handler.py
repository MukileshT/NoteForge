from pathlib import Path
from typing import List
from pdf2image import convert_from_path
from utils.logger import get_logger

logger = get_logger(__name__)

class PDFHandler:
    def __init__(self, dpi: int = 300):
        self.dpi = dpi
    
    def pdf_to_images(self, pdf_path: Path) -> List[Path]:
        try:
            images = convert_from_path(str(pdf_path), dpi=self.dpi)
            temp_dir = Path("temp_pages")
            temp_dir.mkdir(exist_ok=True)
            image_paths = []
            for idx, img in enumerate(images):
                temp_path = temp_dir / f"{pdf_path.stem}_page_{idx+1}.png"
                img.save(temp_path, "PNG")
                image_paths.append(temp_path)
            return image_paths
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            raise
