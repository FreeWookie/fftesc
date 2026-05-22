#!/bin/bash
# Build FFTESC Tool as a single executable bundle
# Usage: ./build_bundle.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "═══════════════════════════════════════════"
echo "  FFTESC Tool — Build Bundle v1.01"
echo "═══════════════════════════════════════════"

# Activate venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

source venv/bin/activate

# Check PyInstaller
if ! python -c "import PyInstaller" 2>/dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf build/ dist/ __pycache__/ gui/__pycache__/ ftesc/__pycache__/

# Build
echo "🔨 Building single executable..."
pyinstaller --clean fftesc_tool.spec

# Result
if [ -f "dist/FFTESC_Tool" ]; then
    SIZE=$(du -h dist/FFTESC_Tool | cut -f1)
    echo ""
    echo "✅ Build successful!"
    echo "   Executable: dist/FFTESC_Tool"
    echo "   Size: $SIZE"
    echo ""
    echo "   Run: ./dist/FFTESC_Tool"
else
    echo "❌ Build failed. Check output above."
    exit 1
fi
