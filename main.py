import sys
import os
import json
from datetime import datetime

# #region agent log
try:
    with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_main_entry", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:8", "message": "Main entry point", "data": {"python_version": sys.version, "python_path": sys.executable}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
except: pass
# #endregion

# Add the 'src' directory to the Python path
# This allows us to import modules from the 'src' directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# #region agent log
try:
    with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_before_import", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:12", "message": "Before importing enhanced_main_window", "data": {"sys_path": sys.path[:3]}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
except: pass
# #endregion

try:
    from gui.enhanced_main_window import main  # pyright: ignore[reportMissingImports]
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_import_success", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:15", "message": "Successfully imported enhanced_main_window", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
    except: pass
    # #endregion
except ImportError as e:
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_import_error", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:18", "message": "ImportError in main", "data": {"error_type": type(e).__name__, "error_msg": str(e), "error_args": e.args}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
    except: pass
    # #endregion
    print(f"Import error: {e}")
    raise
except Exception as e:
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_other_error", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:25", "message": "Other error in main", "data": {"error_type": type(e).__name__, "error_msg": str(e), "error_args": e.args}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
    except: pass
    # #endregion
    print(f"Error: {e}")
    raise

if __name__ == "__main__":
    # #region agent log
    try:
        with open(r"v:\dev\projects\Python\Claude\obsidian_notes_converter\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": f"log_{int(datetime.now().timestamp() * 1000)}_calling_main", "timestamp": int(datetime.now().timestamp() * 1000), "location": "main.py:32", "message": "Calling main()", "data": {}, "sessionId": "debug-session", "runId": "run1", "hypothesisId": "ALL"}) + "\n")
    except: pass
    # #endregion
    main()
