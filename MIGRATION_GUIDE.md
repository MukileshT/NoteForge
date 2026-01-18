# Migration Guide: Stabilized Project Setup

## For New Users

### Quick Start
```bash
# 1. Clone and enter directory
git clone <repo_url>
cd obsidian_notes_converter

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up PaddleOCR
python scripts/setup_paddleocr.py

# 5. Run the application
python main.py
```

That's it! The application will:
- Validate PaddleOCR installation
- Fall back to EasyOCR if needed
- Show clear error messages if something is missing

---

## For Existing Users (Upgrading)

### If You're on `main` Branch

```bash
# 1. Stash any uncommitted changes
git stash

# 2. Switch to the stabilized branch
git checkout refactor/dependency-bootstrap

# 3. Recreate your virtual environment (recommended)
deactivate  # if currently active
rm -rf .venv  # or: Remove-Item -Recurse -Force .venv (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run setup script
python scripts/setup_paddleocr.py

# 6. Test the application
python main.py
```

### If You Have Custom Modifications

1. **Check the changes:**
   ```bash
   git diff main refactor/dependency-bootstrap
   ```

2. **Key files that changed:**
   - `main.py` - New startup validation
   - `scripts/setup_paddleocr.py` - Complete rewrite
   - `requirements.txt` - Now has actual content
   - `src/ocr/local_engines.py` - Added compatibility checks
   - New files: `src/ocr/paddle_resolver.py`, `.env.example`

3. **Merge strategy:**
   ```bash
   git checkout refactor/dependency-bootstrap
   git checkout main <your-custom-file>
   # Manually merge if needed
   ```

---

## Environment Variables (Optional)

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Custom PaddleOCR path (if not using default location)
PADDLEOCR_HOME=/path/to/paddleocr

# OCR mode
OCR_MODE=local
```

---

## Troubleshooting

### "PaddleOCR installation incomplete"

**Cause:** PaddleOCR packages not installed or incompatible version.

**Fix:**
```bash
python scripts/setup_paddleocr.py
```

Or manually:
```bash
pip install --force-reinstall paddleocr==3.3.2 paddlepaddle==2.6.2
```

### "set_optimization_level" Error

**Cause:** Paddle API version mismatch.

**Fix:**
```bash
pip install --force-reinstall paddlepaddle==2.6.2
```

The application will now detect this issue at startup and warn you.

### "DLL load failed" on Windows

**Cause:** Missing Visual C++ Redistributables or incompatible torch/paddle binaries.

**Fix:**
1. Install [Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
2. The application will automatically use EasyOCR fallback

### EasyOCR is slow

**Cause:** Running on CPU instead of GPU.

**Fix:** Install CUDA-enabled versions if you have an NVIDIA GPU:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

---

## What Changed?

### ✓ Improvements
- **One-command setup:** `python scripts/setup_paddleocr.py`
- **Automatic fallback:** Uses EasyOCR if PaddleOCR fails
- **Clear error messages:** Tells you exactly what to do
- **No hardcoded paths:** Everything uses config or environment variables
- **Version validation:** Detects incompatibilities before runtime
- **Clean dependencies:** Removed 20 unused imports

### → Unchanged
- Application functionality
- API key management
- GUI interface
- Output format
- Configuration files (except new .env support)

### ✖ Removed
- Manual PADDLEOCR_HOME path hacks
- Hardcoded Windows paths
- Unused import clutter
- Silent failures

---

## Rollback (If Needed)

If you encounter issues and need to revert:

```bash
git checkout stable-pre-cleanup
```

Or return to main:
```bash
git checkout main
```

Please report any issues so we can fix them!

---

## Verification

Verify the setup is working:

```bash
# Check Python dependencies
pip list | findstr paddle

# Verify no import errors
python -c "from src.ocr.paddle_resolver import resolve_paddleocr_path; print(resolve_paddleocr_path())"

# Run the setup script in test mode
python scripts/setup_paddleocr.py

# Start the application
python main.py
```

---

## Next Steps

1. Run the application and process a document
2. Check the logs in `logs/` directory
3. Review `STABILIZATION_SUMMARY.md` for detailed changes
4. Provide feedback or report issues

---

## Questions?

- Review: `STABILIZATION_SUMMARY.md`
- Check: `README.md` (updated with new setup)
- See: `.env.example` for configuration options