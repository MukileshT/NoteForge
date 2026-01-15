import json
import os
from typing import Any, Dict, Optional

class RunState:
    def __init__(self, log_dir: str):
        self.state_path = os.path.join(log_dir, "run_state.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"last_completed_page": None, "errors": []}

    def update(self, last_completed_page: Optional[int] = None, error: Optional[str] = None):
        if last_completed_page is not None:
            self.state["last_completed_page"] = last_completed_page
        if error:
            self.state["errors"].append(error)
        self._save()

    def _save(self):
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def get_last_completed_page(self) -> Optional[int]:
        return self.state.get("last_completed_page")

    def get_errors(self):
        return self.state.get("errors", [])
