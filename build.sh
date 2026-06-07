#!/bin/bash
# Build script for Python Manta library
# This script builds the Go CGO shared library and prepares the Python package

set -e

echo "🔨 Building Python Manta Library"
echo "=================================="

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed or not in PATH"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Sync the manta dependency (go_wrapper/manta) to the version locked in .manta-version
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/tools/prepare_manta.sh"

echo "✅ Prerequisites check passed"

# Build Go CGO shared library
echo ""
echo "🏗️  Building Go CGO shared library..."
cd go_wrapper

# Clean previous builds
rm -f libmanta_wrapper.so libmanta_wrapper.h

# Build shared library
echo "   Tidying Go modules..."
go mod tidy

echo "   Building shared library..."
go build -buildmode=c-shared -o libmanta_wrapper.so .

if [ ! -f "libmanta_wrapper.so" ]; then
    echo "❌ Failed to build shared library"
    exit 1
fi

if [ ! -f "libmanta_wrapper.h" ]; then
    echo "❌ Header file not generated"
    exit 1
fi

echo "✅ Shared library built successfully"

# Copy to Python package
echo "   Copying to Python package..."
cp libmanta_wrapper.so ../src/python_manta/
cp libmanta_wrapper.h ../src/python_manta/

cd ..

# Verify Python imports
echo ""
echo "🐍 Verifying Python package..."
cd src

# Try to use uv if available and we're in a project with dependencies
if command -v uv &> /dev/null && [ -f "../../pyproject.toml" ]; then
    echo "   Using uv environment..."
    if cd ../.. && uv run python -c "import sys; sys.path.insert(0, 'python_manta/src'); import python_manta; print(f'Package version: {python_manta.__version__}')"; then
        echo "✅ Python package imports successfully"
        cd python_manta/src
    else
        echo "❌ Python package import failed with uv"
        cd python_manta/src
        exit 1
    fi
else
    echo "   Using system Python..."
    if python3 -c "import python_manta; print(f'Package version: {python_manta.__version__}')"; then
        echo "✅ Python package imports successfully"
    else
        echo "❌ Python package import failed"
        echo "   Note: Make sure pydantic is installed: pip install pydantic"
        exit 1
    fi
fi

cd ..

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "📦 Package structure:"
find . -name "*.py" -o -name "*.so" -o -name "*.h" | sort

echo ""
echo "🚀 Ready to use Python Manta!"
echo "   Example: python3 examples/basic_usage.py [demo_file.dem]"