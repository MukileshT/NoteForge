import os
import json
from src.logging.run_state import RunState

class ResumeManager:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.run_state = RunState(log_dir)

    def has_incomplete_run(self) -> bool:
        return os.path.exists(os.path.join(self.log_dir, "run_state.json"))

    def prompt_resume(self) -> bool:
        # Placeholder: Replace with GUI/CLI prompt as needed
        response = input("Previous run detected. Resume? (y/n): ")
        return response.strip().lower() == 'y'

    def get_last_completed_page(self):
        return self.run_state.get_last_completed_page()

    def load_logged_ocr(self, page_index: int) -> dict:
        filename = os.path.join(self.log_dir, f"page_{page_index:02d}_ocr.json")
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
