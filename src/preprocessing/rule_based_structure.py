"""Rule-Based Text Structuring (No LLM Tokens)"""
import re
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

class RuleBasedStructurer:
    """Apply structure to text using rules (no AI/LLM)"""
    
    def __init__(self):
        # Header patterns
        self.header_patterns = [
            (r'^#+\s+(.+)$', 0),  # Already markdown headers
            (r'^([A-Z][A-Z\s]{2,})$', 2),  # ALL CAPS = h2
            (r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:?$', 3),  # Title Case = h3
            (r'^(\d+\.\s+[A-Z].+)$', 3),  # Numbered sections
        ]
        
        # Symbol mappings
        self.symbol_map = {
            'ⓘ': '> [!info]',
            '⚠': '> [!warning]',
            '!': '> [!important]',
            '✓': '> [!success]',
            '✗': '> [!failure]',
            '?': '> [!question]',
            '→': '→',  # Keep arrows
            '←': '←',
            '↔': '↔',
        }
        
        # Flow diagram patterns
        self.flow_patterns = [
            r'(.+?)\s*→\s*(.+)',  # A → B
            r'(.+?)\s*←\s*(.+)',  # A ← B
            r'(.+?)\s*↔\s*(.+)',  # A ↔ B
        ]
        
        # Math patterns (to clean/normalize)
        self.math_patterns = [
            (r'\b([a-zA-Z])\s*=\s*(.+)', r'$\1 = \2$'),  # Variable equations
            (r'([\d\.]+)\s*([+\-*/×÷])\s*([\d\.]+)', r'$\1 \2 \3$'),  # Math operations
            (r'\^(\d+)', r'^{\1}'),  # Exponents
            (r'_([a-zA-Z0-9]+)', r'_{\1}'),  # Subscripts
        ]
    
    def structure(self, text: str) -> str:
        """Apply all rule-based structuring
        
        Args:
            text: Raw text to structure
        
        Returns:
            Structured markdown text
        """
        lines = text.split('\n')
        structured_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                structured_lines.append('')
                continue
            
            # Apply transformations
            line = self._apply_headers(line)
            line = self._apply_symbols(line)
            line = self._apply_flow_diagrams(line)
            line = self._normalize_math(line)
            
            structured_lines.append(line)
        
        # Join and clean up
        result = '\n'.join(structured_lines)
        result = self._cleanup(result)
        
        logger.debug(f"Structured {len(lines)} lines")
        return result
    
    def _apply_headers(self, line: str) -> str:
        """Detect and format headers"""
        for pattern, level in self.header_patterns:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                # Don't re-header already formatted headers
                if line.startswith('#'):
                    return line
                
                header_text = match.group(1) if match.lastindex else line
                return f"{'#' * level} {header_text}"
        
        return line
    
    def _apply_symbols(self, line: str) -> str:
        """Convert symbols to callouts"""
        for symbol, replacement in self.symbol_map.items():
            if line.startswith(symbol):
                # Remove symbol and create callout
                content = line[len(symbol):].strip()
                if replacement.startswith('> [!'):
                    return f"{replacement}\n> {content}"
                else:
                    return f"{replacement} {content}"
        
        return line
    
    def _apply_flow_diagrams(self, line: str) -> str:
        """Convert flow diagrams to structured lists"""
        for pattern in self.flow_patterns:
            match = re.match(pattern, line)
            if match:
                parts = [p.strip() for p in match.groups()]
                # Convert to nested list
                result = f"- {parts[0]}\n"
                for part in parts[1:]:
                    result += f"  - {part}\n"
                return result.strip()
        
        return line
    
    def _normalize_math(self, line: str) -> str:
        """Normalize math notation"""
        for pattern, replacement in self.math_patterns:
            line = re.sub(pattern, replacement, line)
        
        return line
    
    def _cleanup(self, text: str) -> str:
        """Clean up formatted text"""
        # Remove excessive blank lines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Fix spacing around headers
        text = re.sub(r'(\n#{1,6}\s+.+)', r'\n\1', text)
        
        # Ensure callouts are properly formatted
        text = re.sub(r'(> \[!\w+\]\n)([^>])', r'\1> \2', text)
        
        return text.strip()
    
    def extract_metadata(self, text: str) -> Dict[str, any]:
        """Extract metadata from text using rules
        
        Returns:
            Dict with 'subject', 'date', 'topics'
        """
        lines = text.split('\n')[:20]  # Check first 20 lines
        
        metadata = {
            'subject': None,
            'date': None,
            'topics': []
        }
        
        # Subject code pattern (e.g., CS101, EE201)
        subject_pattern = r'\b([A-Z]{2,4}\d{3,4})\b'
        
        # Date patterns
        date_patterns = [
            r'\b(\d{4})-(\d{2})-(\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{2})/(\d{2})/(\d{4})\b',  # DD/MM/YYYY
            r'\b(\d{2})\.(\d{2})\.(\d{4})\b',  # DD.MM.YYYY
        ]
        
        for line in lines:
            # Extract subject code
            if not metadata['subject']:
                match = re.search(subject_pattern, line)
                if match:
                    metadata['subject'] = match.group(1)
            
            # Extract date
            if not metadata['date']:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        metadata['date'] = match.group(0)
                        break
            
            # Extract topics (headers in first few lines)
            if line.startswith('#'):
                topic = re.sub(r'^#+\s+', '', line).strip()
                if topic and len(topic) > 3:
                    metadata['topics'].append(topic)
        
        return metadata
