#!/bin/bash
# Simple build script for PDF Coordinate Viewer
# This script builds the executable using the Python build script

echo "🚀 Building PDF Coordinate Viewer executable..."
echo "================================================"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed or not in PATH"
    echo "   Please install uv first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
uv sync --dev

# Run the build script
echo ""
echo "🔨 Building executable..."
uv run python build.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Build completed successfully!"
    echo "📁 Executable: dist/PDF-Coordinate-Viewer"
    echo "📦 Portable package: PDF-Coordinate-Viewer-Portable/"
    echo ""
    echo "💡 You can now run: ./dist/PDF-Coordinate-Viewer"
    echo "   Or distribute the portable package folder"
else
    echo "❌ Build failed. Please check the error messages above."
    exit 1
fi 