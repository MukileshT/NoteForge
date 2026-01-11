import json
from core.note_session import NoteSession
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class TextCleaner:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
    
    def clean_session(self, session: NoteSession):
        for page in session.pages:
            self._clean_page(page)

    def _clean_page(self, page):
        blocks_to_clean = [{"index": i, "text": block.content} for i, block in enumerate(page.text_blocks)]
        
        if not blocks_to_clean:
            return

        prompt = f'''Fix ONLY spelling and missing words in the following JSON array of text blocks.
Return a JSON array with corrections. For each block, provide the index and the corrected text.
If a block is correct, you don't need to include it in the response.

Input:
{json.dumps(blocks_to_clean, indent=2)}

Output:
'''
        try:
            result = self.ai_client.analyze_text(prompt)
            
            if isinstance(result, list):
                for correction in result:
                    idx = correction.get('index')
                    corrected_text = correction.get('corrected')
                    if idx is not None and corrected_text is not None:
                        if 0 <= idx < len(page.text_blocks):
                            page.text_blocks[idx].content = corrected_text
        except Exception as e:
            logger.error(f"Failed to clean page {page.page_number}: {e}")
