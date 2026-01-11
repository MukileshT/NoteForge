# Fix all imports - save as fix_all_imports.ps1

# Fix config_manager.py
@"
import yaml
from pathlib import Path
from typing import Any, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            'ai_provider': 'anthropic',
            'subject_code_pattern': r'^[A-Z]{2}\d{3}`$',
            'date_formats': ['%Y-%m-%d'],
            'vault': {'notes_folder': 'Notes', 'assets_folder': 'assets'}
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def load_symbols(self) -> Dict[str, Any]:
        try:
            with open("data/symbols.yaml", 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {'symbols': {}, 'rendering': {}}
"@ | Out-File -FilePath "src/core/config_manager.py" -Encoding UTF8

# Fix pipeline.py
@"
from pathlib import Path
from typing import List, Callable

from core.note_session import NoteSession, PageContent
from core.config_manager import ConfigManager
from preprocessing.pdf_handler import PDFHandler
from preprocessing.page_normalizer import PageNormalizer
from preprocessing.metadata_extractor import MetadataExtractor
from vision.ocr_engine import OCREngine
from vision.block_classifier import BlockClassifier
from vision.diagram_detector import DiagramDetector
from processing.label_matcher import LabelMatcher
from processing.image_optimizer import ImageOptimizer
from processing.text_cleaner import TextCleaner
from markdown.composer import MarkdownComposer
from markdown.cross_reference import CrossReferenceLinker
from vault.file_writer import VaultWriter
from vault.index_manager import IndexManager
from utils.logger import get_logger

logger = get_logger(__name__)

class ProcessingPipeline:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.pdf_handler = PDFHandler()
        self.page_normalizer = PageNormalizer()
        self.metadata_extractor = MetadataExtractor(config)
        self.ocr_engine = OCREngine(config)
        self.block_classifier = BlockClassifier(config)
        self.diagram_detector = DiagramDetector(config)
        self.label_matcher = LabelMatcher(config)
        self.image_optimizer = ImageOptimizer(config)
        self.text_cleaner = TextCleaner(config)
        self.markdown_composer = MarkdownComposer(config)
        self.cross_reference_linker = CrossReferenceLinker()
        self.vault_writer = VaultWriter(config)
        self.index_manager = IndexManager(config)
    
    def process(self, input_files: List[Path], vault_path: Path, 
                progress_callback: Callable = None) -> NoteSession:
        def update(msg: str, pct: float):
            logger.info(f"[{int(pct*100)}%] {msg}")
            if progress_callback:
                progress_callback(msg, pct)
        
        try:
            update("Normalizing pages...", 0.05)
            page_images = self._prepare_pages(input_files)
            if not page_images:
                raise ValueError("No valid pages found")
            
            update("Extracting metadata...", 0.15)
            metadata = self.metadata_extractor.extract(page_images[0])
            session = NoteSession(subject=metadata['subject'], date=metadata['date'], 
                                topics=metadata.get('topics', []))
            
            total = len(page_images)
            for idx, page_img in enumerate(page_images):
                pct = 0.20 + (0.50 * (idx / total))
                update(f"Processing page {idx+1}/{total}...", pct)
                page_content = self._process_single_page(page_img, idx+1)
                session.pages.append(page_content)
            
            update("Matching labels...", 0.70)
            self.label_matcher.match_labels(session)
            
            update("Optimizing images...", 0.75)
            self.image_optimizer.optimize_session_images(session, vault_path)
            
            update("Cleaning text...", 0.80)
            self.text_cleaner.clean_session(session)
            
            update("Composing markdown...", 0.85)
            markdown = self.markdown_composer.compose(session)
            
            update("Cross-references...", 0.90)
            markdown = self.cross_reference_linker.process(markdown, session)
            
            update("Updating index...", 0.95)
            self.index_manager.update_index(session, vault_path)
            
            update("Writing to vault...", 0.97)
            self.vault_writer.write(session, markdown, vault_path)
            
            update("Complete!", 1.0)
            return session
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _prepare_pages(self, input_files: List[Path]) -> List[Path]:
        all_pages = []
        for file_path in input_files:
            if file_path.suffix.lower() == '.pdf':
                pages = self.pdf_handler.pdf_to_images(file_path)
                all_pages.extend(pages)
            else:
                all_pages.append(file_path)
        normalized = []
        for page in all_pages:
            normalized.append(self.page_normalizer.normalize(page))
        return normalized
    
    def _process_single_page(self, page_image: Path, page_number: int) -> PageContent:
        page_content = PageContent(page_number=page_number, raw_image_path=page_image)
        ocr_result = self.ocr_engine.process_page(page_image)
        page_content.text_blocks = ocr_result['text_blocks']
        diagrams = self.diagram_detector.detect(page_image)
        page_content.diagram_regions = diagrams
        classified = self.block_classifier.classify(page_image, ocr_result)
        page_content.formula_blocks = classified.get('formulas', [])
        page_content.symbols = classified.get('symbols', [])
        return page_content
"@ | Out-File -FilePath "src/core/pipeline.py" -Encoding UTF8

# Fix pdf_handler.py
@"
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
"@ | Out-File -FilePath "src/preprocessing/pdf_handler.py" -Encoding UTF8

# Fix page_normalizer.py
@"
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
"@ | Out-File -FilePath "src/preprocessing/page_normalizer.py" -Encoding UTF8

# Fix metadata_extractor.py
@"
from pathlib import Path
from typing import Dict, Optional
from vision.ai_client import AIClient
from utils.validators import validate_subject_code, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

class MetadataExtractor:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
        self.subject_pattern = config.get('subject_code_pattern')
        self.date_formats = config.get('date_formats')
    
    def extract(self, first_page: Path, user_provided: Optional[Dict] = None) -> Dict:
        if user_provided:
            subject = user_provided.get('subject')
            date_str = user_provided.get('date')
            if subject and validate_subject_code(subject, self.subject_pattern):
                parsed_date = parse_date(date_str, self.date_formats) if date_str else None
                if parsed_date:
                    return {'subject': subject, 'date': parsed_date.date(), 'topics': []}
        metadata = self._extract_from_image(first_page)
        if not metadata['subject'] or not validate_subject_code(metadata['subject'], self.subject_pattern):
            raise ValueError("Invalid subject code")
        if not metadata['date']:
            raise ValueError("Invalid date")
        return metadata
    
    def _extract_from_image(self, image_path: Path) -> Dict:
        prompt = f'''Extract from this handwritten notes first page:
1. Subject code (format: {self.subject_pattern})
2. Date
3. Main topics (max 3)

Return ONLY JSON:
{{
    "subject": "EC301",
    "date": "2026-01-11",
    "topics": ["topic1"]
}}'''
        try:
            result = self.ai_client.analyze_image(image_path, prompt)
            date_str = result.get('date')
            parsed_date = parse_date(date_str, self.date_formats) if date_str else None
            return {
                'subject': result.get('subject'),
                'date': parsed_date.date() if parsed_date else None,
                'topics': result.get('topics', [])
            }
        except:
            return {'subject': None, 'date': None, 'topics': []}
"@ | Out-File -FilePath "src/preprocessing/metadata_extractor.py" -Encoding UTF8

# Fix ai_client.py
@"
import json
import base64
from pathlib import Path
from typing import Dict, Any
import anthropic
import openai
import google.generativeai as genai
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    def __init__(self, config):
        self.config = config
        self.provider = config.get('ai_provider')
        api_key = config.get('ai_api_key')
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            raise ValueError("API key not configured")
        if self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = config.get('anthropic_model')
        elif self.provider == 'openai':
            openai.api_key = api_key
            self.model = config.get('openai_model')
        elif self.provider == 'gemini':
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.get('gemini_model', 'gemini-2.0-flash-exp'))
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def analyze_image(self, image_path: Path, prompt: str) -> Dict[str, Any]:
        image_data = self._encode_image(image_path)
        try:
            if self.provider == 'anthropic':
                response = self._call_anthropic(image_data, prompt)
            elif self.provider == 'openai':
                response = self._call_openai(image_data, prompt)
            else:
                response = self._call_gemini(image_path, prompt)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    def _encode_image(self, path: Path) -> str:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _call_anthropic(self, image_data: str, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        return msg.content[0].text
    
    def _call_openai(self, image_data: str, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, image_path: Path, prompt: str) -> str:
        from PIL import Image
        img = Image.open(image_path)
        response = self.model.generate_content([prompt, img])
        return response.text
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)
        return json.loads(response)
"@ | Out-File -FilePath "src/vision/ai_client.py" -Encoding UTF8

Write-Host "All imports fixed! Now run: python main.py" -ForegroundColor Green