from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Dict, Any
from pathlib import Path

@dataclass
class TextBlock:
    content: str
    bbox: Dict[str, float]
    confidence: float = 1.0
    symbol_meaning: Optional[str] = None

@dataclass
class DiagramRegion:
    bbox: Dict[str, float]
    label: Optional[str] = None
    caption: Optional[str] = None
    image_path: Optional[Path] = None
    diagram_type: str = "diagram"

@dataclass
class FormulaBlock:
    content: str
    bbox: Dict[str, float]
    latex: Optional[str] = None

@dataclass
class PageContent:
    page_number: int
    raw_image_path: Path
    text_blocks: List[TextBlock] = field(default_factory=list)
    diagram_regions: List[DiagramRegion] = field(default_factory=list)
    formula_blocks: List[FormulaBlock] = field(default_factory=list)

@dataclass
class NoteSession:
    subject: str
    date: date
    pages: List[PageContent] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    source_type: str = "handwritten"
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.subject:
            raise ValueError("Subject code required")
        if not self.date:
            raise ValueError("Date required")
    
    @property
    def filename_base(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d")
        if self.topics:
            topic_str = "-".join(self.topics[:3]).replace(" ", "-")[:50]
        else:
            topic_str = "Notes"
        return f"{self.subject}_{date_str}_{topic_str}"
    
    @property
    def markdown_filename(self) -> str:
        return f"{self.filename_base}.md"
    
    @property
    def assets_folder(self) -> str:
        return self.filename_base
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)
    
    def get_all_diagrams(self) -> List[DiagramRegion]:
        diagrams = []
        for page in self.pages:
            diagrams.extend(page.diagram_regions)
        return diagrams
