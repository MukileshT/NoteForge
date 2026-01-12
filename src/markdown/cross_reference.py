import re
from core.note_session import NoteSession

class CrossReferenceLinker:
    def process(self, markdown: str, session: NoteSession) -> str:
        labels = [d.label for d in session.get_all_diagrams() if d.label]
        for label in labels:
            pattern = r'\b' + re.escape(label) + r'\b'
            anchor = label.replace('.', '-')
            replacement = f"[{label}](#{anchor})"
            markdown = re.sub(pattern, replacement, markdown)
        return markdown
