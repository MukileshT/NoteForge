import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Load environment variables from .env if present
load_dotenv(override=True)

# Add the 'src' directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import path resolver after sys.path setup
from ocr.paddle_resolver import (
    resolve_paddleocr_path,
    validate_paddleocr_installation,
    check_pip_installation,
    get_setup_instructions
)

# Startup validation with fail-fast
print("Checking dependencies...")

# Check if PaddleOCR is installed via pip
is_pip_available, paddle_ver, paddleocr_ver = check_pip_installation()

if is_pip_available:
    print(f"[OK] PaddleOCR (pip): paddle={paddle_ver}, paddleocr={paddleocr_ver}")
else:
    # Try local path resolution
    resolved_paddle_path = resolve_paddleocr_path()
    if resolved_paddle_path:
        os.environ["PADDLEOCR_HOME"] = str(resolved_paddle_path)
        if validate_paddleocr_installation(resolved_paddle_path):
            print("[OK] PaddleOCR (local)")
        else:
            print("[WARN] PaddleOCR incomplete - will use EasyOCR fallback")
    else:
        print("[INFO] PaddleOCR not installed - will use EasyOCR fallback")
        print(get_setup_instructions())

try:
    from gui.enhanced_main_window import main  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    raise
except Exception as e:
    print(f"[ERROR] {e}")
    raise

if __name__ == "__main__":
    main()
