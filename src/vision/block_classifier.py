from pathlib import Path
from typing import Dict, List
import re
from core.note_session import FormulaBlock
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class BlockClassifier:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
        symbols_config = config.load_symbols()
        self.known_symbols = symbols_config.get('symbols', {})
    
    def classify(self, image_path: Path, ocr_result: Dict) -> Dict:
        formulas = self._detect_formulas(ocr_result['text_blocks'])
        self._detect_symbols(ocr_result['text_blocks'])
        return {'formulas': formulas}
    
    def _detect_formulas(self, text_blocks: List) -> List[FormulaBlock]:
        formulas = []
        patterns = [r'[∫∑∏√∂∇]', r'\d+[\+\-\*/]\d+', r'[a-z]\s*=\s*', r'\^']
        for block in text_blocks:
            for pattern in patterns:
                if re.search(pattern, block.content):
                    formulas.append(FormulaBlock(content=block.content, bbox=block.bbox))
                    break
        return formulas
    
    def _detect_symbols(self, text_blocks: List) -> None:
        for block in text_blocks:
            for symbol, meaning in self.known_symbols.items():
                if block.content.strip().startswith(symbol):
                    block.symbol_meaning = meaning
                    block.content = block.content.strip()[len(symbol):].strip()
                    break
