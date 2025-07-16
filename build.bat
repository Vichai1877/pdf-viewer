@echo off
REM Simple build script for PDF Coordinate Viewer (Windows)
REM This script builds the executable using the Python build script

echo 🚀 Building PDF Coordinate Viewer executable...
echo ================================================

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: uv is not installed or not in PATH
    echo    Please install uv first: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Install dependencies if needed
echo 📦 Installing dependencies...
uv sync --dev

REM Run the build script
echo.
echo 🔨 Building executable...
uv run python build.py

REM Check if build was successful
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Build completed successfully!
    echo 📁 Executable: dist\PDF-Coordinate-Viewer.exe
    echo 📦 Portable package: PDF-Coordinate-Viewer-Portable\
    echo.
    echo 💡 You can now run: dist\PDF-Coordinate-Viewer.exe
    echo    Or distribute the portable package folder
) else (
    echo ❌ Build failed. Please check the error messages above.
    pause
    exit /b 1
)

pause 