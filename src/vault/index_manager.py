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
