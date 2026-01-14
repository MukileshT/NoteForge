import logging
import sys
from pathlib import Path


def get_logger(name: str, debug_log_path: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Console: INFO and above
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File: DEBUG and above to configurable path
        if debug_log_path is None:
            # Read raw config file if present to avoid importing ConfigManager (prevents circular import)
            try:
                import json
                cfg_path = Path('config') / 'app_config.json'
                if cfg_path.exists():
                    with open(cfg_path, 'r', encoding='utf-8') as f:
                        cfg = json.load(f)
                        debug_log = cfg.get('logging', {}).get('debug_log_path')
                        if debug_log:
                            debug_log_path = Path(debug_log)
                        else:
                            debug_log_path = Path('logs') / 'debug.log'
                else:
                    debug_log_path = Path('logs') / 'debug.log'
            except Exception:
                debug_log_path = Path('logs') / 'debug.log'
        else:
            debug_log_path = Path(debug_log_path)
        debug_log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(debug_log_path), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    return logger
