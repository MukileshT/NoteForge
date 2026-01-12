from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAML is required but not installed. "
        "Install with: pip install pyyaml"
    ) from None

from utils.logger import get_logger

logger = get_logger(__name__)

class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        return {
            'ai_provider': 'anthropic',
            'subject_code_pattern': r'^[A-Z]{2}\d{3}$',
            'date_formats': ['%Y-%m-%d'],
            'vault': {'notes_folder': 'Notes', 'assets_folder': 'assets'}
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value
    
    def load_symbols(self) -> Dict[str, Any]:
        try:
            with open("data/symbols.yaml", 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except:
            return {'symbols': {}, 'rendering': {}}
