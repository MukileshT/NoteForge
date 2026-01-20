@echo off
echo ========================================
echo Cleaning Development Files
echo ========================================
echo.

echo Removing PowerShell scripts...
del /q *.ps1 2>nul

echo Removing converter log...
del /q converter.log 2>nul

echo Removing cache directories...
if exist .ruff_cache rmdir /s /q .ruff_cache 2>nul
if exist context rmdir /s /q context 2>nul
if exist offline_pkgs rmdir /s /q offline_pkgs 2>nul
if exist temp_pages rmdir /s /q temp_pages 2>nul
if exist third_party rmdir /s /q third_party 2>nul

echo Removing Python cache...
for /d /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i"
del /s /q *.pyc 2>nul

echo Removing build artifacts...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist *.spec.backup del /q *.spec.backup 2>nul

echo.
echo ========================================
echo Cleanup complete!
echo ========================================
echo.
echo Project is now production-ready.
echo Run build.bat to create the executable.
echo.
pause
