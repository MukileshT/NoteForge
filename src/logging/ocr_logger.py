import json
import os
from datetime import datetime
from typing import Any

class OCRLogger:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def log_page_ocr(self, page_index: int, ocr_mode: str, engine: str, confidence: float, raw_blocks: Any, structured_text: str):
        data = {
            "page_index": page_index,
            "ocr_mode": ocr_mode,
            "engine": engine,
            "confidence": confidence,
            "raw_blocks": raw_blocks,
            "structured_text": structured_text,
            "timestamp": datetime.now().isoformat(timespec='seconds')
        }
        filename = os.path.join(self.log_dir, f"page_{page_index:02d}_ocr.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
