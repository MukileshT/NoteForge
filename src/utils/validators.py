import re
from datetime import datetime
from typing import Optional, List
from dateutil import parser as date_parser

def validate_subject_code(subject: str, pattern: str = r'^[A-Z]{2}\d{3}$') -> bool:
    return bool(re.match(pattern, subject))

def parse_date(date_str: str, formats: Optional[List[str]] = None) -> Optional[datetime]:
    if formats is None:
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    try:
        return date_parser.parse(date_str, dayfirst=True)
    except:
        return None

def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    return sanitized.strip('_')

def validate_label(label: str, pattern: str = r'\b(fig|figure|grp|gr|graph)\s*\d+\.\d+[a-z]?\b') -> bool:
    return bool(re.search(pattern, label, re.IGNORECASE))

def extract_label_info(label: str) -> Optional[dict]:
    pattern = r'\b(fig|figure|grp|gr|graph)\s*(\d+)\.(\d+)([a-z])?\b'
    match = re.search(pattern, label, re.IGNORECASE)
    if not match:
        return None
    label_type = match.group(1).lower()
    major = match.group(2)
    minor = match.group(3)
    suffix = match.group(4)
    if label_type in ['fig', 'figure']:
        label_type = 'fig'
    elif label_type in ['grp', 'gr', 'graph']:
        label_type = 'graph'
    return {
        'type': label_type,
        'number': f"{major}.{minor}",
        'suffix': suffix,
        'full': f"{label_type}{major}.{minor}{suffix or ''}"
    }
