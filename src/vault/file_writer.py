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
