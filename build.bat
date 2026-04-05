@echo off
echo ========================================
echo NoteForge - Build Script
echo ========================================
echo.

REM Activate virtual environment
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate
) else (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv .venv
    pause
    exit /b 1
)

REM Install PyInstaller if not present
echo Installing/Updating PyInstaller...
pip install --upgrade pyinstaller
echo.

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM Build the executable
echo Building executable...
pyinstaller build_exe.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build complete!
    echo ========================================
    echo Executable location: dist\NoteForge.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    echo.
)

pause
