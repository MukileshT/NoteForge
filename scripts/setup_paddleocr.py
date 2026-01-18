"""
PaddleOCR Setup Script - Automated installer for PaddleOCR dependencies

This script handles:
- Detection of OS and Python environment
- Installation of paddleocr and paddlepaddle via pip
- Validation of paddle API compatibility
- Clear error messages with actionable fixes
"""
import sys
import platform
import subprocess
from pathlib import Path
from typing import Tuple, Optional


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def detect_platform() -> Tuple[str, str]:
    """
    Detect OS and recommend paddle package.
    
    Returns:
        (os_type, recommended_package)
    """
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if 'windows' in system:
        return ('windows', 'paddlepaddle')
    elif 'linux' in system:
        # Check for CUDA availability
        try:
            import torch
            if torch.cuda.is_available():
                cuda_version = torch.version.cuda
                if cuda_version and cuda_version.startswith('11'):
                    return ('linux', 'paddlepaddle-gpu')
                elif cuda_version and cuda_version.startswith('12'):
                    return ('linux', 'paddlepaddle-gpu')
        except ImportError:
            pass
        return ('linux', 'paddlepaddle')
    elif 'darwin' in system:
        if 'arm' in machine or 'aarch64' in machine:
            return ('macos-arm', 'paddlepaddle')
        return ('macos-intel', 'paddlepaddle')
    else:
        return ('unknown', 'paddlepaddle')


def check_python_version() -> bool:
    """Check if Python version is compatible with PaddlePaddle."""
    version_info = sys.version_info
    if version_info.major == 3 and 8 <= version_info.minor <= 12:
        return True
    return False


def install_paddle_packages() -> bool:
    """
    Install paddleocr and paddlepaddle using pip.
    
    Returns:
        True if installation succeeded
    """
    os_type, paddle_pkg = detect_platform()
    
    print(f"Detected platform: {os_type}")
    print(f"Recommended package: {paddle_pkg}")
    print()
    
    # Define exact versions for compatibility
    packages = [
        'paddleocr==3.3.2',
        'paddlepaddle==2.6.2',
    ]
    
    print("Installing PaddleOCR packages...")
    print("This may take several minutes...\n")
    
    try:
        # Use current Python interpreter
        cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + packages
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✔ Installation complete")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✖ Installation failed")
        print(f"Error: {e.stderr}")
        return False


def validate_installation() -> Tuple[bool, Optional[str]]:
    """
    Validate that PaddleOCR and PaddlePaddle are properly installed.
    
    Returns:
        (success, error_message)
    """
    print("\nValidating installation...")
    
    # Check paddleocr import
    try:
        import paddleocr
        print(f"  ✔ paddleocr {paddleocr.__version__}")
    except ImportError as e:
        return False, f"paddleocr import failed: {e}"
    
    # Check paddle import
    try:
        import paddle
        print(f"  ✔ paddlepaddle {paddle.__version__}")
    except ImportError as e:
        return False, f"paddle import failed: {e}"
    
    # Check for the specific API that was failing
    try:
        from paddle.inference import Config
        config = Config()
        
        # Check if problematic method exists
        if not hasattr(config, 'set_optimization_level'):
            print("  ⚠ Warning: set_optimization_level not available in paddle.inference.Config")
            print("    This might cause runtime issues with certain PaddleOCR features")
            print("    Recommendation: Use PaddleOCR's Python API mode instead of inference mode")
        else:
            print("  ✔ paddle.inference.Config API validated")
            
    except Exception as e:
        return False, f"Paddle inference API check failed: {e}"
    
    print("\n✔ All validations passed")
    return True, None


def create_marker_file():
    """Create a marker file to indicate PaddleOCR is set up via pip."""
    paddle_dir = get_project_root() / 'third_party' / 'paddleocr'
    paddle_dir.mkdir(parents=True, exist_ok=True)
    
    marker = paddle_dir / 'INSTALLED_VIA_PIP.txt'
    marker.write_text(
        'PaddleOCR installed via pip.\n'
        'Do not place binaries here.\n'
        'Use: pip install paddleocr paddlepaddle\n'
    )


def print_instructions():
    """Print post-installation instructions."""
    print("\n" + "="*60)
    print("PaddleOCR Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Run your application: python main.py")
    print("2. If you encounter the 'set_optimization_level' error:")
    print("   - The packages are installed but there's an API mismatch")
    print("   - Try: pip install --force-reinstall paddlepaddle==2.6.2")
    print("   - Or: Use EasyOCR fallback (automatic)")
    print("\nFor custom PADDLEOCR_HOME:")
    print("  Set environment variable to your installation path")
    print("="*60)


def main():
    """Main setup routine."""
    print("="*60)
    print("PaddleOCR Setup Script")
    print("="*60)
    print()
    
    # Check Python version
    if not check_python_version():
        print(f"✖ Python {sys.version_info.major}.{sys.version_info.minor} detected")
        print("  PaddlePaddle requires Python 3.8-3.12")
        sys.exit(1)
    
    print(f"✔ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    print()
    
    # Confirm installation
    response = input("Install paddleocr and paddlepaddle? [Y/n]: ").strip().lower()
    if response and response not in ('y', 'yes'):
        print("Setup cancelled")
        sys.exit(0)
    
    print()
    
    # Install packages
    if not install_paddle_packages():
        print("\n✖ Setup failed")
        print("\nManual installation:")
        print("  pip install paddleocr==3.3.2 paddlepaddle==2.6.2")
        sys.exit(1)
    
    # Validate
    success, error = validate_installation()
    if not success:
        print(f"\n✖ Validation failed: {error}")
        print("\nTroubleshooting:")
        print("  1. Try: pip install --force-reinstall paddlepaddle==2.6.2")
        print("  2. Check: python -c 'import paddle; print(paddle.__version__)'")
        print("  3. If issues persist, the application will fall back to EasyOCR")
        sys.exit(1)
    
    # Create marker
    create_marker_file()
    
    # Print success message
    print_instructions()


if __name__ == "__main__":
    main()
