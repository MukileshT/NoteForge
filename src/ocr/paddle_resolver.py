"""PaddleOCR Path Resolver - Config-driven path management"""
import os
from pathlib import Path
from typing import Optional


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


def validate_paddleocr_installation(paddle_path: Path) -> bool:
    """
    Validate that PaddleOCR installation is complete.
    
    Args:
        paddle_path: Path to PaddleOCR directory
        
    Returns:
        True if installation appears valid
    """
    if not paddle_path.exists():
        return False
    
    # Check for essential files/directories
    # This is a basic check - adjust based on actual PaddleOCR structure
    required_indicators = [
        paddle_path / "paddleocr",  # Python package
    ]
    
    return any(indicator.exists() for indicator in required_indicators)


def get_setup_instructions() -> str:
    """Get user-friendly setup instructions."""
    return """
PaddleOCR not found. To set it up:

Option 1 (Recommended):
    python scripts/setup_paddleocr.py

Option 2 (Manual):
    pip install paddleocr paddlepaddle
    
Option 3 (Custom Path):
    Set PADDLEOCR_HOME environment variable to your installation path
"""
