"""
PaddleOCR Setup Script - Simplified Windows Installation

This script provides multiple installation methods:
1. [RECOMMENDED] Pre-tested pip packages with compatibility fixes
2. Minimal install with older stable versions
3. Skip PaddleOCR (use EasyOCR only)

For Windows users, PaddleOCR has known issues with:
- DLL loading failures
- API version mismatches
- Complex dependency chains

This script attempts to work around these issues.
"""
import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def print_header():
    """Print script header."""
    print()
    print("=" * 60)
    print("  PaddleOCR Setup Script")
    print("=" * 60)
    print()


def detect_platform() -> Tuple[str, str, str]:
    """
    Detect OS, architecture, and Python version.
    
    Returns:
        (os_type, arch, python_version)
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    if 'windows' in system:
        arch = 'x64' if '64' in machine or 'amd64' in machine else 'x86'
        return ('windows', arch, py_version)
    elif 'linux' in system:
        arch = 'x64' if '64' in machine else 'x86'
        return ('linux', arch, py_version)
    elif 'darwin' in system:
        arch = 'arm64' if 'arm' in machine else 'x64'
        return ('macos', arch, py_version)
    else:
        return ('unknown', machine, py_version)


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and 8 <= minor <= 12:
        return True
    return False


def check_existing_paddle() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if PaddleOCR is already installed and working.
    
    Returns:
        (is_working, paddle_version, paddleocr_version)
    """
    try:
        import paddle
        paddle_ver = paddle.__version__
    except ImportError:
        return False, None, None
    
    try:
        import paddleocr
        paddleocr_ver = paddleocr.__version__
    except ImportError:
        return False, paddle_ver, None
    
    # Test if it actually works
    try:
        from paddle.inference import Config
        config = Config()
        # This is the problematic method
        if hasattr(config, 'set_optimization_level'):
            return True, paddle_ver, paddleocr_ver
        else:
            return False, paddle_ver, paddleocr_ver
    except Exception:
        return False, paddle_ver, paddleocr_ver


def uninstall_paddle():
    """Uninstall existing paddle packages to start fresh."""
    print("Removing existing PaddlePaddle installations...")
    packages = ['paddlepaddle', 'paddlepaddle-gpu', 'paddleocr', 'paddlex']
    
    for pkg in packages:
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'uninstall', '-y', pkg],
                capture_output=True,
                text=True
            )
        except Exception:
            pass
    
    print("  Done")


def install_method_standard() -> bool:
    """
    Install tested pip packages with known-good versions.
    
    This uses specific versions that are tested to work together.
    """
    print("\n[Method: Standard pip install]")
    print("-" * 40)
    
    os_type, arch, py_ver = detect_platform()
    
    # Determine packages based on platform
    if os_type == 'windows':
        # For Windows, use CPU-only paddle with specific versions
        # Use older paddleocr that has better Windows compatibility
        packages = [
            'paddlepaddle==2.5.2',  # More stable version for Windows
            'paddleocr==2.7.3',     # Older stable version
        ]
    else:
        packages = [
            'paddlepaddle==2.6.2',
            'paddleocr==3.3.2',
        ]
    
    print(f"Platform: {os_type} ({arch})")
    print(f"Python: {py_ver}")
    print(f"Packages: {', '.join(packages)}")
    print()
    
    # Uninstall existing first
    uninstall_paddle()
    
    print("\nInstalling packages (this may take several minutes)...")
    
    for pkg in packages:
        print(f"  Installing {pkg}...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pkg, '--quiet'],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            if result.returncode != 0:
                print(f"    Failed: {result.stderr[:200]}")
                return False
            print(f"    OK")
        except subprocess.TimeoutExpired:
            print(f"    Timeout - installation took too long")
            return False
        except Exception as e:
            print(f"    Error: {e}")
            return False
    
    return True


def install_method_minimal() -> bool:
    """
    Install minimal paddle packages for basic OCR only.
    
    This uses very old but stable versions.
    """
    print("\n[Method: Minimal installation]")
    print("-" * 40)
    
    # Uninstall existing
    uninstall_paddle()
    
    print("Installing minimal PaddleOCR...")
    
    try:
        # Install just paddlepaddle and paddleocr with very old stable versions
        packages = [
            'paddlepaddle==2.4.2',
            'paddleocr==2.6.1.3',
        ]
        
        for pkg in packages:
            print(f"  Installing {pkg}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pkg, '--quiet'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                print(f"    Failed: {result.stderr[:200]}")
                return False
            print(f"    OK")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def validate_installation() -> bool:
    """Validate that PaddleOCR works correctly."""
    print("\n[Validation]")
    print("-" * 40)
    
    # Check paddle
    try:
        import paddle
        print(f"  paddle: {paddle.__version__}")
    except ImportError as e:
        print(f"  paddle: FAILED - {e}")
        return False
    except Exception as e:
        print(f"  paddle: ERROR - {e}")
        return False
    
    # Check paddleocr
    try:
        import paddleocr
        print(f"  paddleocr: {paddleocr.__version__}")
    except ImportError as e:
        print(f"  paddleocr: FAILED - {e}")
        return False
    except Exception as e:
        print(f"  paddleocr: ERROR - {e}")
        return False
    
    # Check inference API (optional - may not exist in older versions)
    try:
        from paddle.inference import Config
        config = Config()
        if hasattr(config, 'set_optimization_level'):
            print(f"  inference API: OK")
        else:
            print(f"  inference API: PARTIAL (some methods missing)")
    except Exception as e:
        print(f"  inference API: SKIPPED - {e}")
    
    # Try to create PaddleOCR instance
    print("\n  Testing PaddleOCR initialization...")
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        print(f"  PaddleOCR instance: OK")
        return True
    except Exception as e:
        print(f"  PaddleOCR instance: FAILED")
        print(f"    Error: {str(e)[:150]}")
        return False


def create_marker_file(method: str):
    """Create a marker file indicating installation method."""
    paddle_dir = get_project_root() / 'third_party' / 'paddleocr'
    paddle_dir.mkdir(parents=True, exist_ok=True)
    
    marker = paddle_dir / 'SETUP_INFO.txt'
    marker.write_text(
        f'PaddleOCR Setup Info\n'
        f'====================\n'
        f'Installation method: {method}\n'
        f'Python version: {sys.version}\n'
        f'Platform: {platform.platform()}\n'
        f'\n'
        f'To reinstall, run: python scripts/setup_paddleocr.py\n'
    )


def print_skip_instructions():
    """Print instructions for skipping PaddleOCR."""
    print("\n" + "=" * 60)
    print("  PaddleOCR Setup Skipped")
    print("=" * 60)
    print()
    print("The application will use EasyOCR as the fallback OCR engine.")
    print("EasyOCR works well for most documents.")
    print()
    print("To enable PaddleOCR later:")
    print("  python scripts/setup_paddleocr.py")
    print()


def print_success():
    """Print success message."""
    print("\n" + "=" * 60)
    print("  PaddleOCR Setup Complete!")
    print("=" * 60)
    print()
    print("You can now run the application:")
    print("  python main.py")
    print()
    print("If you encounter issues:")
    print("  1. The app will automatically fall back to EasyOCR")
    print("  2. Run: python scripts/setup_paddleocr.py --repair")
    print()


def print_failure():
    """Print failure message with alternatives."""
    print("\n" + "=" * 60)
    print("  PaddleOCR Setup Failed")
    print("=" * 60)
    print()
    print("Don't worry! The application can still work without PaddleOCR.")
    print("It will use EasyOCR as a fallback OCR engine.")
    print()
    print("To run with EasyOCR only:")
    print("  python main.py")
    print()
    print("To retry PaddleOCR setup:")
    print("  python scripts/setup_paddleocr.py --repair")
    print()
    print("Common issues on Windows:")
    print("  - Missing Visual C++ Redistributable")
    print("    Download: https://aka.ms/vs/17/release/vc_redist.x64.exe")
    print("  - Incompatible Python version (need 3.8-3.11)")
    print("  - Antivirus blocking DLL loading")
    print()


def main():
    """Main setup routine."""
    print_header()
    
    os_type, arch, py_ver = detect_platform()
    
    # Check Python version
    if not check_python_version():
        print(f"ERROR: Python {py_ver} is not supported")
        print(f"PaddlePaddle requires Python 3.8 - 3.12")
        print()
        print("Options:")
        print("  1. Install Python 3.10 or 3.11 (recommended)")
        print("  2. Skip PaddleOCR and use EasyOCR only")
        sys.exit(1)
    
    print(f"System: {os_type} ({arch})")
    print(f"Python: {py_ver}")
    print()
    
    # Check if --repair flag is passed
    repair_mode = '--repair' in sys.argv
    
    # Check existing installation
    if not repair_mode:
        is_working, paddle_ver, paddleocr_ver = check_existing_paddle()
        if is_working:
            print(f"PaddleOCR is already installed and working!")
            print(f"  paddle: {paddle_ver}")
            print(f"  paddleocr: {paddleocr_ver}")
            print()
            response = input("Reinstall anyway? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("Setup cancelled.")
                sys.exit(0)
    
    # Show menu
    print("Installation options:")
    print()
    print("  [1] Standard install (recommended)")
    print("      Uses tested package versions")
    print()
    print("  [2] Minimal install")
    print("      Older, more stable versions")
    print()
    print("  [3] Skip PaddleOCR")
    print("      Use EasyOCR only (no PaddleOCR)")
    print()
    
    choice = input("Select option [1/2/3]: ").strip()
    
    if choice == '3':
        print_skip_instructions()
        create_marker_file("skipped")
        sys.exit(0)
    
    # Try installation
    success = False
    method = "unknown"
    
    if choice == '2':
        success = install_method_minimal()
        method = "minimal"
    else:
        # Default: standard install
        success = install_method_standard()
        method = "standard"
    
    if success:
        # Validate
        if validate_installation():
            create_marker_file(method)
            print_success()
            sys.exit(0)
        else:
            print("\nInstallation completed but validation failed.")
            print("Trying minimal installation as fallback...")
            
            if install_method_minimal():
                if validate_installation():
                    create_marker_file("minimal-fallback")
                    print_success()
                    sys.exit(0)
    
    # All methods failed
    create_marker_file("failed")
    print_failure()
    sys.exit(1)


if __name__ == "__main__":
    main()
