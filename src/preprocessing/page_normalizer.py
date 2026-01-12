from pathlib import Path
from PIL import Image
import cv2
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

class PageNormalizer:
    def normalize(self, image_path: Path) -> Path:
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img = self._deskew(cv_img)
            img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            normalized_path = image_path.parent / f"normalized_{image_path.name}"
            img.save(normalized_path, "PNG")
            return normalized_path
        except:
            return image_path
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
            if lines is not None:
                angles = []
                for rho, theta in lines[:, 0]:
                    angle = np.degrees(theta) - 90
                    if abs(angle) < 10:
                        angles.append(angle)
                if angles:
                    median_angle = np.median(angles)
                    if abs(median_angle) > 0.5:
                        h, w = image.shape[:2]
                        M = cv2.getRotationMatrix2D((w//2, h//2), median_angle, 1.0)
                        image = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        except:
            pass
        return image
