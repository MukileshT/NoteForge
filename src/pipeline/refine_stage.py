from typing import Optional

class RefineStage:
    def __init__(self, api_key: Optional[str] = None, enabled: bool = False):
        self.api_key = api_key
        self.enabled = enabled and bool(api_key)

    def refine(self, structured_text: str) -> str:
        if not self.enabled:
            return structured_text
        # Placeholder: Call LLM API for refinement
        # Only send structured_text, never images or coordinates
        # Simulate LLM output for now
        return structured_text + "\n[Refined by LLM]"
