import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(override=True)

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import path resolver after sys.path setup
from ocr.paddle_resolver import (
    resolve_paddleocr_path,
    validate_paddleocr_installation,
    get_setup_instructions
)

# Startup validation with fail-fast
print("Checking dependencies...")

# Set PADDLEOCR_HOME if resolved
resolved_paddle_path = resolve_paddleocr_path()
if resolved_paddle_path:
    os.environ["PADDLEOCR_HOME"] = str(resolved_paddle_path)
    if validate_paddleocr_installation(resolved_paddle_path):
        print("✔ PaddleOCR found")
    else:
        print("✖ PaddleOCR installation incomplete")
        print(get_setup_instructions())
        # Allow to continue with EasyOCR fallback
else:
    print("⚠ PaddleOCR not configured (will use EasyOCR)")
    print(get_setup_instructions())
    # Allow to continue with fallback

try:
    from gui.enhanced_main_window import main  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(f"✖ Import error: {e}")
    raise
except Exception as e:
    print(f"✖ Error: {e}")
    raise

if __name__ == "__main__":
    main()
