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
