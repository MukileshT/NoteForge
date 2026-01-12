# Fix remaining files with relative imports

# Fix ocr_engine.py
@"
from pathlib import Path
from typing import Dict, List
import pytesseract
from PIL import Image
import cv2
import numpy as np
from core.note_session import TextBlock
from utils.logger import get_logger

logger = get_logger(__name__)

class OCREngine:
    def __init__(self, config):
        self.config = config
    
    def process_page(self, image_path: Path) -> Dict:
        try:
            img = Image.open(image_path)
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv_img = self._preprocess(cv_img)
            ocr_data = pytesseract.image_to_data(cv_img, output_type=pytesseract.Output.DICT)
            text_blocks = self._extract_blocks(ocr_data, img.size)
            full_text = pytesseract.image_to_string(cv_img)
            return {'text_blocks': text_blocks, 'full_text': full_text.strip()}
        except:
            return {'text_blocks': [], 'full_text': ''}
    
    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    def _extract_blocks(self, ocr_data: Dict, img_size: tuple) -> List[TextBlock]:
        blocks = []
        w, h = img_size
        current = []
        bbox = None
        for i in range(len(ocr_data['text'])):
            if int(ocr_data['conf'][i]) < 30:
                continue
            text = ocr_data['text'][i].strip()
            if not text:
                continue
            x = ocr_data['left'][i] / w
            y = ocr_data['top'][i] / h
            bw = ocr_data['width'][i] / w
            bh = ocr_data['height'][i] / h
            if bbox is None:
                bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current = [text]
            elif abs(y - bbox['y']) < 0.01:
                right = max(bbox['x'] + bbox['width'], x + bw)
                bbox['width'] = right - bbox['x']
                current.append(text)
            else:
                if current:
                    blocks.append(TextBlock(content=' '.join(current), bbox=bbox))
                bbox = {'x': x, 'y': y, 'width': bw, 'height': bh}
                current = [text]
        if current:
            blocks.append(TextBlock(content=' '.join(current), bbox=bbox))
        return blocks
"@ | Out-File -FilePath "src/vision/ocr_engine.py" -Encoding UTF8

# Fix block_classifier.py
@"
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
        symbols = self._detect_symbols(ocr_result['full_text'])
        return {'formulas': formulas, 'symbols': symbols}
    
    def _detect_formulas(self, text_blocks: List) -> List[FormulaBlock]:
        formulas = []
        patterns = [r'[∫∑∏√∂∇]', r'\d+[\+\-\*/]\d+', r'[a-z]\s*=\s*', r'\^']
        for block in text_blocks:
            for pattern in patterns:
                if re.search(pattern, block.content):
                    formulas.append(FormulaBlock(content=block.content, bbox=block.bbox))
                    break
        return formulas
    
    def _detect_symbols(self, text: str) -> List[Dict]:
        found = []
        for symbol, meaning in self.known_symbols.items():
            if symbol in text:
                found.append({'symbol': symbol, 'meaning': meaning})
        return found
"@ | Out-File -FilePath "src/vision/block_classifier.py" -Encoding UTF8

# Fix diagram_detector.py
@"
from pathlib import Path
from typing import List
from core.note_session import DiagramRegion
from vision.ai_client import AIClient
from utils.logger import get_logger

logger = get_logger(__name__)

class DiagramDetector:
    def __init__(self, config):
        self.config = config
        self.ai_client = AIClient(config)
    
    def detect(self, image_path: Path) -> List[DiagramRegion]:
        prompt = '''Detect all diagrams, graphs, circuits, or drawings in this image.
Return ONLY JSON array:
[
    {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "type": "circuit"},
    ...
]
Coordinates are normalized 0-1. type: diagram, graph, circuit, table'''
        try:
            result = self.ai_client.analyze_image(image_path, prompt)
            if isinstance(result, list):
                regions = []
                for r in result:
                    regions.append(DiagramRegion(
                        bbox={'x': r['x'], 'y': r['y'], 'width': r['width'], 'height': r['height']},
                        diagram_type=r.get('type', 'diagram')
                    ))
                return regions
            return []
        except:
            return []
"@ | Out-File -FilePath "src/vision/diagram_detector.py" -Encoding UTF8

# Fix label_matcher.py
@"
from typing import Dict
import re
from core.note_session import NoteSession, DiagramRegion
from utils.validators import extract_label_info
from utils.geometry import BoundingBox, calculate_nearest_box
from utils.logger import get_logger

logger = get_logger(__name__)

class LabelMatcher:
    def __init__(self, config):
        self.config = config
        self.label_pattern = config.get('label_matching.label_pattern')
        self.max_distance_mult = config.get('label_matching.max_distance_multiplier', 1.5)
        self.direction_priority = config.get('label_matching.direction_priority')
    
    def match_labels(self, session: NoteSession):
        for page in session.pages:
            self._match_page(page, session)
    
    def _match_page(self, page, session):
        labels = self._find_labels(page.text_blocks)
        diagrams = page.diagram_regions
        if not labels or not diagrams:
            return
        label_counts = {}
        for label_text, label_bbox in labels:
            info = extract_label_info(label_text)
            if not info:
                continue
            label_box = BoundingBox(label_bbox['x'], label_bbox['y'], label_bbox['width'], label_bbox['height'])
            diagram_boxes = [BoundingBox(d.bbox['x'], d.bbox['y'], d.bbox['width'], d.bbox['height']) for d in diagrams]
            max_dist = label_box.height * self.max_distance_mult
            idx, nearest, dist = calculate_nearest_box(label_box, diagram_boxes, max_dist, self.direction_priority)
            if idx is not None:
                base_label = info['full']
                if base_label in label_counts:
                    label_counts[base_label] += 1
                    final_label = f"{base_label}{chr(96 + label_counts[base_label])}"
                    session.add_warning(f"Duplicate label {base_label}, renamed to {final_label}")
                else:
                    label_counts[base_label] = 0
                    final_label = base_label
                diagrams[idx].label = final_label
    
    def _find_labels(self, text_blocks) -> list:
        labels = []
        for block in text_blocks:
            matches = re.finditer(self.label_pattern, block.content, re.IGNORECASE)
            for match in matches:
                labels.append((match.group(0), block.bbox))
        return labels
"@ | Out-File -FilePath "src/processing/label_matcher.py" -Encoding UTF8

# Fix image_optimizer.py
@"
from pathlib import Path
from PIL import Image
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class ImageOptimizer:
    def __init__(self, config):
        self.config = config
        self.max_w = config.get('image_optimization.max_diagram_width', 1200)
        self.max_h = config.get('image_optimization.max_diagram_height', 1200)
        self.quality = config.get('image_optimization.diagram_quality', 85)
    
    def optimize_session_images(self, session: NoteSession, vault_path: Path):
        assets_dir = vault_path / self.config.get('vault.assets_folder') / session.assets_folder
        assets_dir.mkdir(parents=True, exist_ok=True)
        for page in session.pages:
            for diagram in page.diagram_regions:
                if diagram.label:
                    optimized = self._optimize_diagram(page.raw_image_path, diagram.bbox, assets_dir, diagram.label)
                    diagram.image_path = optimized
    
    def _optimize_diagram(self, source: Path, bbox: dict, output_dir: Path, label: str) -> Path:
        img = Image.open(source)
        w, h = img.size
        x1 = int(bbox['x'] * w)
        y1 = int(bbox['y'] * h)
        x2 = int((bbox['x'] + bbox['width']) * w)
        y2 = int((bbox['y'] + bbox['height']) * h)
        cropped = img.crop((x1, y1, x2, y2))
        if cropped.width > self.max_w or cropped.height > self.max_h:
            cropped.thumbnail((self.max_w, self.max_h), Image.LANCZOS)
        filename = f"{label.replace('.', '_')}.png"
        output_path = output_dir / filename
        cropped.save(output_path, "PNG", optimize=True, quality=self.quality)
        return output_path
"@ | Out-File -FilePath "src/processing/image_optimizer.py" -Encoding UTF8

# Fix text_cleaner.py
@"
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
            for block in page.text_blocks:
                cleaned = self._clean_text(block.content)
                if cleaned != block.content:
                    block.content = cleaned
    
    def _clean_text(self, text: str) -> str:
        prompt = f'''Fix ONLY spelling and missing words in: "{text}"
Return JSON: {{"corrected": "fixed text"}}
Do NOT rephrase or improve grammar.'''
        try:
            result = self.ai_client.analyze_image(None, prompt)
            return result.get('corrected', text)
        except:
            return text
"@ | Out-File -FilePath "src/processing/text_cleaner.py" -Encoding UTF8

# Fix composer.py
@"
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class MarkdownComposer:
    def __init__(self, config):
        self.config = config
        self.symbols_config = config.load_symbols()
    
    def compose(self, session: NoteSession) -> str:
        md = self._frontmatter(session)
        md += "\n\n"
        for page in session.pages:
            md += self._compose_page(page)
        return md
    
    def _frontmatter(self, session: NoteSession) -> str:
        topics_str = ', '.join(session.topics) if session.topics else ''
        return f"""---
subject: {session.subject}
date: {session.date.strftime('%Y-%m-%d')}
topics: [{topics_str}]
source: {session.source_type}
---"""
    
    def _compose_page(self, page) -> str:
        md = ""
        for block in page.text_blocks:
            md += f"{block.content}\n\n"
        for diagram in page.diagram_regions:
            if diagram.label and diagram.image_path:
                anchor = diagram.label.replace('.', '-')
                caption = diagram.caption or diagram.label
                rel_path = f"assets/{diagram.image_path.parent.name}/{diagram.image_path.name}"
                md += f'<a id="{anchor}"></a>\n'
                md += f"![{caption}]({rel_path})\n\n"
        for formula in page.formula_blocks:
            md += f"$$\n{formula.content}\n$$\n\n"
        for symbol in page.symbols:
            rendering = self.symbols_config.get('rendering', {}).get(symbol['meaning'], {})
            prefix = rendering.get('prefix', '')
            if prefix:
                md += f"{prefix}\n{symbol['symbol']}\n\n"
        return md
"@ | Out-File -FilePath "src/markdown/composer.py" -Encoding UTF8

# Fix cross_reference.py
@"
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
"@ | Out-File -FilePath "src/markdown/cross_reference.py" -Encoding UTF8

# Fix file_writer.py
@"
from pathlib import Path
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class VaultWriter:
    def __init__(self, config):
        self.config = config
        self.notes_folder = config.get('vault.notes_folder', 'Notes')
    
    def write(self, session: NoteSession, markdown: str, vault_path: Path):
        notes_dir = vault_path / self.notes_folder
        notes_dir.mkdir(parents=True, exist_ok=True)
        md_path = notes_dir / session.markdown_filename
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        logger.info(f"Written: {md_path}")
"@ | Out-File -FilePath "src/vault/file_writer.py" -Encoding UTF8

# Fix index_manager.py
@"
import json
from pathlib import Path
from core.note_session import NoteSession
from utils.logger import get_logger

logger = get_logger(__name__)

class IndexManager:
    def __init__(self, config):
        self.config = config
        self.index_file = config.get('vault.index_file', 'vault_index.json')
    
    def update_index(self, session: NoteSession, vault_path: Path):
        index_path = vault_path / self.index_file
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {}
        index[session.subject] = {
            'date': session.date.isoformat(),
            'topics': session.topics,
            'file': session.markdown_filename
        }
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2)
"@ | Out-File -FilePath "src/vault/index_manager.py" -Encoding UTF8

# Update requirements.txt to use new Gemini package
@"
pillow>=10.0.0
pypdf2>=3.0.0
pyyaml>=6.0
python-dateutil>=2.8.2
regex>=2023.0.0
pytesseract>=0.3.10
opencv-python>=4.8.0
pdf2image>=1.16.0
openai>=1.0.0
anthropic>=0.8.0
google-genai>=0.1.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

# Update ai_client.py to use new package
@"
import json
import base64
from pathlib import Path
from typing import Dict, Any
import anthropic
import openai
from google import genai
from utils.logger import get_logger

logger = get_logger(__name__)

class AIClient:
    def __init__(self, config):
        self.config = config
        self.provider = config.get('ai_provider')
        api_key = config.get('ai_api_key')
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            raise ValueError("API key not configured")
        if self.provider == 'anthropic':
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = config.get('anthropic_model')
        elif self.provider == 'openai':
            openai.api_key = api_key
            self.model = config.get('openai_model')
        elif self.provider == 'gemini':
            self.client = genai.Client(api_key=api_key)
            self.model_name = config.get('gemini_model', 'gemini-2.5-flash')
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def analyze_image(self, image_path: Path, prompt: str) -> Dict[str, Any]:
        try:
            if self.provider == 'anthropic':
                image_data = self._encode_image(image_path)
                response = self._call_anthropic(image_data, prompt)
            elif self.provider == 'openai':
                image_data = self._encode_image(image_path)
                response = self._call_openai(image_data, prompt)
            else:
                response = self._call_gemini(image_path, prompt)
            return self._parse_json(response)
        except Exception as e:
            logger.error(f"AI failed: {e}")
            raise
    
    def _encode_image(self, path: Path) -> str:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _call_anthropic(self, image_data: str, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        return msg.content[0].text
    
    def _call_openai(self, image_data: str, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]
            }],
            max_tokens=1024
        )
        return response.choices[0].message.content
    
    def _call_gemini(self, image_path: Path, prompt: str) -> str:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, {'mime_type': 'image/png', 'data': image_data}]
        )
        return response.text
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)
        return json.loads(response)
"@ | Out-File -FilePath "src/vision/ai_client.py" -Encoding UTF8

Write-Host "✅ All files fixed!" -ForegroundColor Green
Write-Host "Run: pip install --upgrade -r requirements.txt" -ForegroundColor Yellow
Write-Host "Then: python main.py" -ForegroundColor Cyan
