"""OpenCV-based Image Preprocessing for OCR"""
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
from utils.logger import get_logger

logger = get_logger(__name__)

class ImagePreprocessor:
    """Preprocess images for optimal OCR performance"""
    
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi
    
    def preprocess(self, image_path: Path) -> np.ndarray:
        """Apply full preprocessing pipeline
        
        Returns:
            Preprocessed image as numpy array
        """
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Deskew
        deskewed = self._deskew(gray)
        
        # Remove margins/borders
        cropped = self._remove_margins(deskewed)
        
        # Resize to target DPI if needed
        resized = self._resize_to_dpi(cropped)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(resized)
        
        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        logger.debug(f"Preprocessed {image_path.name}: shape={thresh.shape}")
        return thresh
    
    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """Correct skew/rotation in image"""
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
        
        angle = cv2.minAreaRect(coords)[-1]
        
        # Correct angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        # Only deskew if angle is significant
        if abs(angle) < 0.5:
            return image
        
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        logger.debug(f"Deskewed by {angle:.2f} degrees")
        return rotated
    
    def _remove_margins(self, image: np.ndarray) -> np.ndarray:
        """Remove white margins around content"""
        # Invert for easier processing
        inv = cv2.bitwise_not(image)
        
        # Find all non-zero points
        coords = cv2.findNonZero(inv)
        if coords is None:
            return image
        
        # Get bounding box
        x, y, w, h = cv2.boundingRect(coords)
        
        # Add small padding
        padding = 10
        x = max(0, x - padding)
        y = max(0, y - padding)
        w = min(image.shape[1] - x, w + 2 * padding)
        h = min(image.shape[0] - y, h + 2 * padding)
        
        return image[y:y+h, x:x+w]
    
    def _resize_to_dpi(self, image: np.ndarray) -> np.ndarray:
        """Resize image to target DPI (approx 300 DPI)"""
        # Assume input is ~150 DPI, scale up to 300 DPI
        scale = 2.0
        
        # Check if image is already large enough
        if image.shape[0] > 2000 or image.shape[1] > 2000:
            scale = 1.0
        
        if scale == 1.0:
            return image
        
        width = int(image.shape[1] * scale)
        height = int(image.shape[0] * scale)
        
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
    
    def preprocess_for_confidence(self, image_path: Path) -> np.ndarray:
        """Lighter preprocessing for confidence checking"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Just denoise and threshold
        denoised = cv2.fastNlMeansDenoising(gray)
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return thresh
