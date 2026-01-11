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
            
            # Process the first page to extract metadata
            first_page_content = self._process_single_page(page_images[0], 1)
            update("Extracting metadata...", 0.15)
            metadata = self.metadata_extractor.extract(first_page_content)
            session = NoteSession(subject=metadata['subject'], date=metadata['date'], 
                                topics=metadata.get('topics', []))
            session.pages.append(first_page_content) # Add first page to session

            total = len(page_images)
            for idx, page_img in enumerate(page_images[1:]): # Start from the second page
                pct = 0.20 + (0.50 * ((idx + 1) / total))
                update(f"Processing page {idx+2}/{total}...", pct)
                page_content = self._process_single_page(page_img, idx+2)
                session.pages.append(page_content)
            
            update("Matching labels...", 0.70)
            self.label_matcher.match_labels(session)
            
            update("Optimizing images...", 0.75)
            self.image_optimizer.optimize_session_images(session, vault_path)
            
            update("Cleaning text...", 0.80)
            self.text_cleaner.clean_session(session)
            
            update("Composing markdown...", 0.85)
            markdown = self.markdown_composer.compose(session)
            
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
        return page_content
