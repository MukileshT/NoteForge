import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, TypeError):
        try:
            import codecs
            if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        except Exception:
            pass  # Continue without UTF-8 reconfiguration

# Load environment variables from .env if present
load_dotenv(override=True)

# Add the 'src' directory to the Python path
try:
    # Try using __file__ first (works in normal execution)
    src_path = Path(__file__).parent / "src"
except (NameError, TypeError):
    # Fallback for PyInstaller bundled executable
    src_path = Path(sys.executable).parent / "src"

# If src doesn't exist in expected location, try current working directory
if not src_path.exists():
    src_path = Path.cwd() / "src"

sys.path.insert(0, str(src_path))

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
