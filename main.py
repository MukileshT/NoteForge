import sys
import os
import json
from datetime import datetime

# Set Paddle / oneDNN compatibility env vars as early as possible
os.environ.setdefault('FLAGS_use_mkldnn', '0')
os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('KMP_DUPLICATE_LIB_OK', 'TRUE')
os.environ.setdefault('FLAGS_use_oneDNN', '0')

# Add the 'src' directory to the Python path
# This allows us to import modules from the 'src' directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

try:
    from gui.enhanced_main_window import main  # pyright: ignore[reportMissingImports]
except ImportError as e:
    print(f"Import error: {e}")
    raise
except Exception as e:
    print(f"Error: {e}")
    raise

if __name__ == "__main__":
    main()
