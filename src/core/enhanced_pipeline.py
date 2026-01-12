"""Enhanced Processing Pipeline with All New Features"""
from pathlib import Path
from typing import List, Callable, Optional

from core.note_session import NoteSession, PageContent
from core.config_manager import ConfigManager
from core.quota_manager import QuotaManager
from preprocessing.pdf_handler import PDFHandler
from preprocessing.page_normalizer import PageNormalizer
from preprocessing.metadata_extractor import MetadataExtractor
from preprocessing.rule_based_structure import RuleBasedStructurer
from ocr.ocr_manager import OCRManager, OCRMode
from vision.diagram_detector_cv import CVDiagramDetector
from llm.provider_factory import ProviderFactory
from processing.label_matcher import LabelMatcher
from processing.image_optimizer import ImageOptimizer
from processing.text_cleaner import TextCleaner
from markdown.composer import MarkdownComposer
from vault.file_writer import VaultWriter
from vault.index_manager import IndexManager
from utils.logger import get_logger

logger = get_logger(__name__)

class EnhancedProcessingPipeline:
    """Enhanced processing pipeline with new features"""
    
    def __init__(self, config, provider_name: str, api_key: str, 
                 model: str = None, ocr_mode=None):
        from llm.provider_factory import ProviderFactory
        from llm.provider_interface import LLMConfig
        from ocr.ocr_manager import OCRManager, OCRMode
        from vision.diagram_detector_cv import CVDiagramDetector
        from preprocessing.rule_based_structure import RuleBasedStructurer
        from core.quota_manager import QuotaManager
        
        self.config = config
        self.quota_manager = QuotaManager()
        
        # Create LLM provider
        self.llm_provider = ProviderFactory.create(
            provider_name=provider_name,
            api_key=api_key,
            model=model or ProviderFactory.get_default_model(provider_name),
            max_tokens=config.get('max_tokens', 1024),
            temperature=config.get('temperature', 0.7),
            base_url=config.get(f'{provider_name}_base_url')
        )
        
        # Initialize OCR manager
        self.ocr_manager = OCRManager(
            mode=ocr_mode,
            tesseract_path=config.get('tesseract_path'),
            confidence_threshold=config.get('ocr_confidence_threshold', 0.6),
            llm_provider=self.llm_provider if ocr_mode == OCRMode.AI else None
        )
        
        # Initialize diagram detector
        self.diagram_detector = CVDiagramDetector()
        
        # Initialize rule-based structurer
        self.rule_structurer = RuleBasedStructurer()
        
        # Initialize quota manager
        self.quota_manager = QuotaManager()
        self.quota_manager.set_limits(
            provider_name,
            max_tokens_per_hour=config.get('max_tokens_per_hour', 100000),
            max_tokens_per_day=config.get('max_tokens_per_day', 1000000),
            max_requests_per_minute=config.get('max_requests_per_minute', 60),
            max_vision_calls_per_hour=config.get('max_vision_calls_per_hour', 100)
        )
        
        logger.info(f"Pipeline initialized with {provider_name} provider, {ocr_mode.value} OCR")
    
    def process(self, input_files: List[Path], vault_path: Path,
                progress_callback: Callable = None) -> NoteSession:
        """Process input files into Obsidian notes
        
        This is the main pipeline that orchestrates all processing steps.
        """
        def update(msg: str, pct: float):
            logger.info(f"[{int(pct*100)}%] {msg}")
            if progress_callback:
                progress_callback(msg, pct)
        
        try:
            update("Initializing...", 0.01)
            
            # Prepare pages
            update("Normalizing pages...", 0.05)
            page_images = self._prepare_pages(input_files)
            if not page_images:
                raise ValueError("No valid pages found")
            
            total_pages = len(page_images)
            logger.info(f"Processing {total_pages} pages")
            
            # Process first page for metadata
            update("Processing first page...", 0.10)
            first_page_content = self._process_single_page(page_images[0], 1)
            
            # Extract metadata using rule-based approach
            update("Extracting metadata...", 0.15)
            metadata = self._extract_metadata_rules(first_page_content)
            
            session = NoteSession(
                subject=metadata['subject'],
                date=metadata['date'],
                topics=metadata.get('topics', [])
            )
            session.pages.append(first_page_content)
            
            # Process remaining pages
            total = len(page_images)
            for idx, page_img in enumerate(page_images[1:], start=2):
                pct = 0.20 + (0.50 * (idx / total))
                update(f"Processing page {idx}/{total}...", pct)
                page_content = self._process_single_page(page_img, idx)
                session.pages.append(page_content)
            
            update("Structuring content...", 0.70)
            self._apply_rule_based_structuring(session)
            
            update("Matching labels...", 0.75)
            self.label_matcher.match_labels(session)
            
            update("Optimizing images...", 0.80)
            self.image_optimizer.optimize_session_images(session, vault_path)
            
            update("Applying final LLM processing...", 0.85)
            self._apply_llm_fixes(session)
            
            update("Composing markdown...", 0.90)
            markdown = self.markdown_composer.compose(session)
            
            update("Updating vault index...", 0.95)
            self.index_manager.update_index(session, vault_path)
            
            update("Writing to vault...", 0.97)
            self.vault_writer.write(session, markdown, vault_path)
            
            # Log quota usage
            usage = self.quota_manager.get_usage(self.provider_name)
            logger.info(f"API Usage - Tokens: {usage['tokens_day']}/{usage['limits']['max_tokens_day']}, "
                       f"Vision calls: {usage['vision_calls_hour']}/{usage['limits']['max_vision_calls_hour']}")
            
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
        """Process a single page with new architecture"""
        page_content = PageContent(page_number=page_number, raw_image_path=page_image)
        
        # Step 1: Detect diagrams (OpenCV)
        diagram_regions = self.cv_diagram_detector.detect(page_image)
        page_content.diagram_regions = diagram_regions
        
        # Step 2: OCR (local or AI)
        ocr_result = self.ocr_manager.extract_text(page_image)
        page_content.text_blocks = ocr_result['text_blocks']
        full_text = ocr_result['full_text']
        
        # Track tokens if AI was used
        if 'tokens_used' in ocr_result:
            self._track_token_usage('ocr', ocr_result['tokens_used'], is_vision=True)
        
        # Step 3: Rule-based structuring (zero tokens)
        structured_text = self.rule_structurer.structure(full_text)
        
        # Step 4: LLM refinement (single call, text-only)
        if self.llm_provider:
            refined_text = self._llm_refine_text(structured_text)
            # Update text blocks with refined content
            # (simplified - in production, would update individual blocks)
            full_text = refined_text
        
        # Store structured text
        page_content.structured_text = structured_text
        
        return page_content
    
    def _llm_refine_text(self, text: str) -> str:
        """Single LLM call to refine structured text"""
        # Check quota
        estimated_tokens = len(text.split()) * 2  # Rough estimate
        if not self.quota_manager.check_quota(self.provider_name, estimated_tokens):
            logger.warning("Quota exceeded, skipping LLM refinement")
            return text
        
        prompt = f"""Refine this text for Obsidian markdown. Fix OCR errors, improve formatting, normalize math notation.

Text:
{text}

Return only the refined markdown text."""
        
        try:
            response = self.llm_provider.complete(prompt)
            self._track_token_usage('refine', response.tokens_used)
            return response.content
        except Exception as e:
            logger.error(f"LLM refinement failed: {e}")
            return text
    
    def _track_token_usage(self, operation: str, tokens: int, is_vision: bool = False):
        """Track and enforce quota"""
        self.quota_manager.record_usage(self.provider_name, tokens, is_vision)
        usage = self.quota_manager.get_usage(self.provider_name)
        logger.info(f"{operation}: {tokens} tokens, "
                   f"total={usage['tokens_hour']}/{usage['limits']['max_tokens_hour']}")
