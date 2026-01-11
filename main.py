import sys
import os

# Add the 'src' directory to the Python path
# This allows us to import modules from the 'src' directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from gui.main_window import main

if __name__ == "__main__":
    main()
