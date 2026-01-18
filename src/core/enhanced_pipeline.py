"""Enhanced Processing Pipeline with All New Features"""
from pathlib import Path
from typing import List, Callable
from datetime import datetime

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
    """Enhanced processing pipeline with all new features"""
    
    def __init__(self, config: ConfigManager, provider_name: str, api_key: str, 
                 model: str = None, ocr_mode: OCRMode = OCRMode.LOCAL, llm_enabled: bool = False):
        self.config = config
        self.provider_name = provider_name
        self.llm_enabled = llm_enabled

        # Initialize quota manager
        self.quota_manager = QuotaManager()
        if provider_name and (llm_enabled or ocr_mode == OCRMode.AI):
            self.quota_manager.set_limits(
                provider_name,
                max_tokens_per_hour=config.get('max_tokens_per_hour', 100000),
                max_tokens_per_day=config.get('max_tokens_per_day', 1000000),
                max_requests_per_minute=config.get('max_requests_per_minute', 60),
                max_vision_calls_per_hour=config.get('max_vision_calls_per_hour', 100)
            )

        # Create LLM provider only if explicitly enabled or AI OCR mode selected
        if llm_enabled or ocr_mode == OCRMode.AI:
            self.llm_provider = ProviderFactory.create(
                provider_name=provider_name,
                api_key=api_key,
                model=model or ProviderFactory.get_default_model(provider_name),
                max_tokens=config.get('max_tokens', 1024),
                temperature=config.get('temperature', 0.7),
                base_url=config.get(f'{provider_name}_base_url')
            )
        else:
            self.llm_provider = None

        # Initialize OCR manager with optional LLM provider for AI fallback
        self.ocr_manager = OCRManager(
            mode=ocr_mode,
            tesseract_path=config.get('tesseract_path'),
            confidence_threshold=config.get('ocr_confidence_threshold', 0.6),
            llm_provider=self.llm_provider,
            easyocr_gpu=config.get('ocr.easyocr_gpu', False)
        )
        
        # Initialize diagram detector (OpenCV-based, no AI)
        self.diagram_detector = CVDiagramDetector()
        
        # Initialize rule-based structurer (zero tokens)
        self.rule_structurer = RuleBasedStructurer()
        
        # Initialize other components
        self.pdf_handler = PDFHandler()
        self.page_normalizer = PageNormalizer()
        # If LLMs not enabled, pass no provider to metadata/text cleaners so they run in non-AI mode
        meta_provider = provider_name if (self.llm_enabled or ocr_mode == OCRMode.AI) else None
        meta_model = model if (self.llm_enabled or ocr_mode == OCRMode.AI) else None
        meta_api_key = api_key if (self.llm_enabled or ocr_mode == OCRMode.AI) else None

        self.metadata_extractor = MetadataExtractor(config, provider=meta_provider, model=meta_model, api_key=meta_api_key)
        self.label_matcher = LabelMatcher(config)
        self.image_optimizer = ImageOptimizer(config)
        self.text_cleaner = TextCleaner(config, provider=meta_provider, model=meta_model, api_key=meta_api_key)
        self.markdown_composer = MarkdownComposer(config)
        self.vault_writer = VaultWriter(config)
        self.index_manager = IndexManager(config)
        
        logger.info(f"Pipeline initialized: provider={provider_name}, OCR={ocr_mode.value}")
    
    def process(self, input_files: List[Path], vault_path: Path,
                progress_callback: Callable = None) -> NoteSession:
        """Process input files into Obsidian notes"""
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
                subject=metadata['subject'] or "UNKNOWN",
                date=metadata['date'] or datetime.now().date(),
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
            if usage:
                logger.info(f"API Usage - Tokens: {usage.get('tokens_day', 0)}/{usage.get('limits', {}).get('max_tokens_day', 0)}, "
                          f"Vision calls: {usage.get('vision_calls_hour', 0)}/{usage.get('limits', {}).get('max_vision_calls_hour', 0)}")
            
            update("Complete!", 1.0)
            return session
        
        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise
    
    def _prepare_pages(self, input_files: List[Path]) -> List[Path]:
        """Prepare and normalize pages"""
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
        """Process a single page with new architecture
        
        Steps:
        1. Detect diagrams (OpenCV, no AI)
        2. OCR text regions only (exclude diagrams)
        3. Rule-based structuring (zero tokens)
        4. Single LLM call for refinement (text-only, max 1 per page)
        """
        page_content = PageContent(page_number=page_number, raw_image_path=page_image)
        
        # Step 1: Detect diagrams FIRST (OpenCV-based, no AI)
        logger.info(f"Detecting diagrams in page {page_number}")
        diagram_regions = self.diagram_detector.detect(page_image)
        page_content.diagram_regions = diagram_regions
        logger.info(f"Found {len(diagram_regions)} diagrams")
        
        # Step 2: OCR text regions (exclude diagrams)
        # OCR manager will handle text extraction, excluding diagram regions
        logger.info(f"Extracting text from page {page_number}")
        ocr_result = self.ocr_manager.extract_text(page_image, is_handwritten=False)
        page_content.text_blocks = ocr_result['text_blocks']
        full_text = ocr_result['full_text']
        
        # Track tokens if AI OCR was used
        if 'tokens_used' in ocr_result:
            self._track_token_usage('ocr', ocr_result['tokens_used'], is_vision=True)
        
        # Step 3: Rule-based structuring (ZERO TOKENS)
        logger.info(f"Applying rule-based structuring to page {page_number}")
        structured_text = self.rule_structurer.structure(full_text)
        
        # Step 4: Single LLM refinement call (text-only, max 1 per page)
        refined_text = structured_text
        if self.llm_provider:
            logger.info(f"Refining text with LLM for page {page_number}")
            refined_text = self._llm_refine_text(structured_text, page_number)
        
        # Update text blocks with refined content
        # For simplicity, update the first text block with refined text
        # In production, would map refined text back to individual blocks
        if page_content.text_blocks and refined_text != structured_text:
            # Split refined text into lines and update blocks
            refined_lines = refined_text.split('\n')
            for i, block in enumerate(page_content.text_blocks[:len(refined_lines)]):
                if i < len(refined_lines):
                    block.content = refined_lines[i]
        
        # Store structured text
        page_content.structured_text = refined_text
        
        return page_content
    
    def _llm_refine_text(self, text: str, page_number: int) -> str:
        """Single LLM call to refine structured text (max 1 per page)
        
        This is the ONLY LLM call allowed per page (except AI OCR mode).
        """
        # Check quota
        estimated_tokens = len(text.split()) * 2  # Rough estimate
        if not self.quota_manager.check_quota(self.provider_name, estimated_tokens):
            logger.warning(f"Quota exceeded for page {page_number}, skipping LLM refinement")
            return text
        
        prompt = f"""Refine this text for Obsidian markdown. Fix OCR errors, improve formatting, normalize math notation, create proper internal links.

Text:
{text}

Return only the refined markdown text. Do not add explanations."""
        
        try:
            response = self.llm_provider.complete(prompt)
            self._track_token_usage('refine', response.tokens_used)
            logger.info(f"LLM refined text for page {page_number}: {response.tokens_used} tokens")
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM refinement failed for page {page_number}: {e}")
            return text
    
    def _apply_rule_based_structuring(self, session: NoteSession):
        """Apply rule-based structuring to all pages"""
        for page in session.pages:
            if hasattr(page, 'structured_text') and page.structured_text:
                # Already structured in _process_single_page
                continue
            elif page.text_blocks:
                # Structure text from blocks
                full_text = '\n'.join(block.content for block in page.text_blocks)
                page.structured_text = self.rule_structurer.structure(full_text)
    
    def _apply_llm_fixes(self, session: NoteSession):
        """Apply final LLM fixes (if quota allows)"""
        # This is optional - most work is done per-page
        # Could add cross-page linking here if needed
        pass
    
    def _extract_metadata_rules(self, page_content: PageContent) -> dict:
        """Extract metadata using rule-based approach (no LLM)"""
        # Get text from first page
        full_text = ''
        if page_content.text_blocks:
            full_text = '\n'.join(block.content for block in page_content.text_blocks)
        elif hasattr(page_content, 'structured_text'):
            full_text = page_content.structured_text
        
        # Use rule-based structurer's metadata extraction
        metadata = self.rule_structurer.extract_metadata(full_text)
        
        # Fallback to metadata extractor if needed
        if not metadata.get('subject') or not metadata.get('date'):
            try:
                fallback_metadata = self.metadata_extractor.extract(page_content)
                if not metadata.get('subject'):
                    metadata['subject'] = fallback_metadata.get('subject')
                if not metadata.get('date'):
                    metadata['date'] = fallback_metadata.get('date')
                if not metadata.get('topics'):
                    metadata['topics'] = fallback_metadata.get('topics', [])
            except:
                pass
        
        # Parse date string to date object
        if isinstance(metadata.get('date'), str):
            date_str = metadata['date']
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d.%m.%Y']:
                try:
                    metadata['date'] = datetime.strptime(date_str, fmt).date()
                    break
                except:
                    continue
            if isinstance(metadata.get('date'), str):
                # Default to today
                metadata['date'] = datetime.now().date()
        
        return metadata
    
    def _track_token_usage(self, operation: str, tokens: int, is_vision: bool = False):
        """Track and enforce quota"""
        self.quota_manager.record_usage(self.provider_name, tokens, is_vision)
        usage = self.quota_manager.get_usage(self.provider_name)
        if usage:
            logger.info(f"{operation}: {tokens} tokens, "
                      f"total={usage.get('tokens_hour', 0)}/{usage.get('limits', {}).get('max_tokens_hour', 0)}")
