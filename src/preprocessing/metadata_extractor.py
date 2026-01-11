from pathlib import Path
from typing import Dict, Optional, List
from vision.ai_client import AIClient
from utils.validators import validate_subject_code, parse_date
from utils.logger import get_logger
from core.note_session import PageContent, TextBlock

logger = get_logger(__name__)

class MetadataExtractor:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
        self.subject_pattern = config.get('subject_code_pattern')
        self.date_formats = config.get('date_formats')
    
    def extract(self, page_content: PageContent, user_provided: Optional[Dict] = None) -> Dict:
        if user_provided:
            subject = user_provided.get('subject')
            date_str = user_provided.get('date')
            if subject and validate_subject_code(subject, self.subject_pattern):
                parsed_date = parse_date(date_str, self.date_formats) if date_str else None
                if parsed_date:
                    return {'subject': subject, 'date': parsed_date.date(), 'topics': []}
        
        metadata = self._extract_from_image(page_content.raw_image_path, page_content.text_blocks)
        
        if not metadata['subject'] or not validate_subject_code(metadata['subject'], self.subject_pattern):
            raise ValueError("Invalid subject code")
        if not metadata['date']:
            raise ValueError("Invalid date")
        
        # Filter out the extracted metadata from the text_blocks
        self._filter_metadata_from_text_blocks(page_content.text_blocks, metadata)
        
        return metadata
    
    def _extract_from_image(self, image_path: Path, text_blocks: List[TextBlock]) -> Dict:
        # Use a more targeted approach for AI extraction, feeding it the raw text
        full_text_content = " ".join([block.content for block in text_blocks])
        prompt = f'''From the following text, extract:
1. Subject code (format: {self.subject_pattern})
2. Date
3. Main topics (max 3)

Text: "{full_text_content}"

Return ONLY JSON:
{{
    "subject": "EC301",
    "date": "2026-01-11",
    "topics": ["topic1"]
}}'''
        try:
            result = self.ai_client.analyze_text(prompt) # Use analyze_text since we're feeding it text
            date_str = result.get('date')
            parsed_date = parse_date(date_str, self.date_formats) if date_str else None
            return {
                'subject': result.get('subject'),
                'date': parsed_date.date() if parsed_date else None,
                'topics': result.get('topics', [])
            }
        except Exception as e:
            logger.error(f"AI failed during metadata extraction: {e}")
            return {'subject': None, 'date': None, 'topics': []}

    def _filter_metadata_from_text_blocks(self, text_blocks: List[TextBlock], metadata: Dict):
        subject_str = metadata['subject']
        date_str = metadata['date'].strftime('%Y-%m-%d')
        
        # Remove text blocks that contain the subject code or date
        # This is a simple filtering, can be made more robust if needed
        text_blocks[:] = [block for block in text_blocks if 
                         subject_str.lower() not in block.content.lower() and
                         date_str not in block.content]
