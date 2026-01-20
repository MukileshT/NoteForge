"""PaddleOCR Path Resolver - Config-driven path management"""
import os
from pathlib import Path
from typing import Optional, Tuple


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def resolve_paddleocr_path() -> Optional[Path]:
    """
    Resolve PaddleOCR installation path using config-driven approach.
    
    Priority:
    1. PADDLEOCR_HOME environment variable
    2. third_party/paddleocr directory in project root
    
    Returns:
        Path to PaddleOCR installation or None if not found
    """
    # Try environment variable first
    env_path = os.getenv("PADDLEOCR_HOME")
    if env_path:
        paddle_path = Path(env_path)
        if paddle_path.exists() and paddle_path.is_dir():
            return paddle_path
    
    # Try local third_party directory
    local_path = get_project_root() / "third_party" / "paddleocr"
    if local_path.exists() and local_path.is_dir():
        # Verify it's not just a placeholder
        has_content = any(local_path.iterdir())
        if has_content:
            return local_path
    
    return None


def check_pip_installation() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if PaddleOCR is installed via pip WITHOUT fully importing it.
    
    This avoids initializing PaddleX (PDX) at startup, which would prevent
    later initialization by PaddleOCREngine.
    
    Returns:
        (is_available, paddle_version, paddleocr_version)
    """
    import importlib.util
    
    paddle_ver = None
    paddleocr_ver = None
    
    # Check if paddle module exists without importing
    paddle_spec = importlib.util.find_spec("paddle")
    if paddle_spec is None:
        return False, None, None
    
    # Get paddle version from metadata (avoids full import)
    try:
        from importlib.metadata import version
        paddle_ver = version("paddlepaddle")
    except Exception:
        # Fallback: try paddlepaddle-gpu
        try:
            from importlib.metadata import version
            paddle_ver = version("paddlepaddle-gpu")
        except Exception:
            paddle_ver = "installed"
    
    # Check if paddleocr module exists without importing
    paddleocr_spec = importlib.util.find_spec("paddleocr")
    if paddleocr_spec is None:
        return False, paddle_ver, None
    
    # Get paddleocr version from metadata (avoids full import)
    try:
        from importlib.metadata import version
        paddleocr_ver = version("paddleocr")
    except Exception:
        paddleocr_ver = "installed"
    
    return True, paddle_ver, paddleocr_ver


def validate_paddleocr_installation(paddle_path: Optional[Path] = None) -> bool:
    """
    Validate that PaddleOCR installation is complete and working.
    
    Args:
        paddle_path: Path to PaddleOCR directory (optional, for local installs)
        
    Returns:
        True if installation appears valid
    """
    # First check if pip installation works
    is_available, paddle_ver, paddleocr_ver = check_pip_installation()
    
    if is_available and paddle_ver and paddleocr_ver:
        return True
    
    # Check local path if provided
    if paddle_path and paddle_path.exists():
        # Check for marker file from setup script
        setup_info = paddle_path / "SETUP_INFO.txt"
        if setup_info.exists():
            content = setup_info.read_text()
            if "skipped" not in content.lower() and "failed" not in content.lower():
                return True
    
    return False


def get_setup_instructions() -> str:
    """Get user-friendly setup instructions."""
    return """
PaddleOCR not found. To set it up:

Option 1 (Recommended):
    python scripts/setup_paddleocr.py

Option 2 (Manual):
    pip install paddlepaddle==2.5.2 paddleocr==2.7.3

Option 3 (Skip - use EasyOCR only):
    The application will automatically use EasyOCR as fallback
"""
