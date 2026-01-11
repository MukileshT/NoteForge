from core.note_session import NoteSession, TextBlock, DiagramRegion, FormulaBlock
from utils.logger import get_logger
import yaml
import re

logger = get_logger(__name__)

class MarkdownComposer:
    def __init__(self, config):
        self.config = config
        self.symbols_config = config.load_symbols()
    
    def compose(self, session: NoteSession) -> str:
        md = self._frontmatter(session)
        md += "\n\n"
        
        labels = [d.label for d in session.get_all_diagrams() if d.label]
        
        for page in session.pages:
            md += self._compose_page(page, labels)
        return md
    
    def _frontmatter(self, session: NoteSession) -> str:
        frontmatter_data = {
            'subject': session.subject,
            'date': session.date.strftime('%Y-%m-%d'),
            'topics': session.topics,
            'source': session.source_type
        }
        return f"---\n{yaml.dump(frontmatter_data)}---"
    
    def _compose_page(self, page, labels) -> str:
        
        all_blocks = []
        all_blocks.extend(page.text_blocks)
        all_blocks.extend(page.diagram_regions)
        all_blocks.extend(page.formula_blocks)

        # Sort blocks by their vertical position, then horizontal
        all_blocks.sort(key=lambda b: (b.bbox['y'], b.bbox['x']))

        md = ""
        for block in all_blocks:
            if isinstance(block, TextBlock):
                content = block.content
                for label in labels:
                    pattern = r'\b' + re.escape(label) + r'\b'
                    anchor = label.replace('.', '-')
                    replacement = f"[{label}](#{anchor})"
                    content = re.sub(pattern, replacement, content)

                if block.symbol_meaning:
                    rendering = self.symbols_config.get('rendering', {}).get(block.symbol_meaning, {})
                    prefix = rendering.get('prefix', '')
                    md += f"{prefix} {content}\n\n"
                else:
                    md += f"{content}\n\n"
            
            elif isinstance(block, DiagramRegion):
                if block.label and block.image_path:
                    anchor = block.label.replace('.', '-')
                    caption = block.caption or self._format_caption(block.label)
                    rel_path = f"assets/{block.image_path.parent.name}/{block.image_path.name}"
                    md += f'<a id="{anchor}"></a>\n'
                    md += f"![{caption}]({rel_path})\n\n"

            elif isinstance(block, FormulaBlock):
                md += f"```latex\n{block.content}\n```\n\n"
        
        return md

    def _format_caption(self, label: str) -> str:
        label = label.lower()
        if label.startswith('fig'):
            kind = 'Figure'
        elif label.startswith('gr'):
            kind = 'Graph'
        elif label.startswith('tbl'):
            kind = 'Table'
        else:
            kind = 'Diagram'

        numbers = re.findall(r'\d+', label)
        if len(numbers) >= 2:
            return f"{kind} {numbers[0]}.{numbers[1]}"
        elif len(numbers) == 1:
            return f"{kind} {numbers[0]}"
        else:
            return label
