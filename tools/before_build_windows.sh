#!/usr/bin/env bash
# Prepare Go toolchain, manta dependency, and build the shared library for Windows wheels.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GO_VERSION=${GO_VERSION:-1.21.5}

echo "Building for Windows AMD64" >&2

# Install Go if not present
if ! command -v go >/dev/null 2>&1; then
    echo "Installing Go ${GO_VERSION} for Windows" >&2
    TEMP_ARCHIVE=$(mktemp --suffix=.zip)
    curl -sSL "https://go.dev/dl/go${GO_VERSION}.windows-amd64.zip" -o "${TEMP_ARCHIVE}"

    # Install to C:\go (standard Windows location)
    mkdir -p /c/go
    unzip -q "${TEMP_ARCHIVE}" -d /c/
    rm -f "${TEMP_ARCHIVE}"

    export PATH="/c/go/bin:${PATH}"
else
    echo "Go already available: $(go version)" >&2
fi

export CGO_ENABLED=1

# Ensure we have MinGW GCC for CGO on Windows
if ! command -v gcc >/dev/null 2>&1; then
    echo "Installing MinGW-w64 for CGO compilation" >&2
    # cibuildwheel usually provides this, but verify
    if ! command -v gcc >/dev/null 2>&1; then
        echo "ERROR: GCC (MinGW) is required for CGO on Windows" >&2
        echo "Please ensure MinGW-w64 is installed" >&2
        exit 1
    fi
fi

# Prepare manta dependency
bash "${ROOT_DIR}/tools/prepare_manta.sh"

# Build the shared library
pushd "${ROOT_DIR}/go_wrapper" >/dev/null

go mod tidy

# Build shared library (DLL on Windows, but we use .so extension for consistency)
# The output will actually be a .dll file but we rename it
go build -buildmode=c-shared -o libmanta_wrapper.dll .

# Rename to .so for Python ctypes consistency across platforms
# (ctypes on Windows can load .dll files named .so)
if [ -f libmanta_wrapper.dll ]; then
    mv libmanta_wrapper.dll libmanta_wrapper.so
fi

popd >/dev/null

# Copy to Python package
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.so" "${ROOT_DIR}/src/python_manta/"
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.h" "${ROOT_DIR}/src/python_manta/"

echo "Windows build preparation complete!" >&2
