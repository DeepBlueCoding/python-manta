#!/usr/bin/env bash
# Prepare Go toolchain, manta dependency, and build the shared library for macOS wheels.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GO_VERSION=${GO_VERSION:-1.21.5}

# Detect architecture
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    GO_ARCH="amd64"
elif [ "$ARCH" = "arm64" ]; then
    GO_ARCH="arm64"
else
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
fi

echo "Building for macOS ${ARCH} (Go: ${GO_ARCH})" >&2

# Install Go if not present
if ! command -v go >/dev/null 2>&1; then
    echo "Installing Go ${GO_VERSION} for ${GO_ARCH}" >&2
    TEMP_ARCHIVE=$(mktemp)
    curl -sSL "https://go.dev/dl/go${GO_VERSION}.darwin-${GO_ARCH}.tar.gz" -o "${TEMP_ARCHIVE}"

    # Install to /usr/local (standard macOS location)
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "${TEMP_ARCHIVE}"
    rm -f "${TEMP_ARCHIVE}"

    export PATH="/usr/local/go/bin:${PATH}"
else
    echo "Go already available: $(go version)" >&2
fi

export CGO_ENABLED=1

# Detect target architecture from cibuildwheel environment
# _PYTHON_HOST_PLATFORM is set by cibuildwheel with the target platform
if [[ -n "${_PYTHON_HOST_PLATFORM:-}" ]]; then
    if [[ "$_PYTHON_HOST_PLATFORM" == *"x86_64"* ]]; then
        TARGET_ARCH="amd64"
        echo "Cross-compiling for x86_64 (from $_PYTHON_HOST_PLATFORM)" >&2
    elif [[ "$_PYTHON_HOST_PLATFORM" == *"arm64"* ]]; then
        TARGET_ARCH="arm64"
        echo "Building for arm64 (from $_PYTHON_HOST_PLATFORM)" >&2
    else
        echo "Warning: Unknown platform $_PYTHON_HOST_PLATFORM, using host architecture" >&2
        TARGET_ARCH="$GO_ARCH"
    fi
else
    echo "Using host architecture: $GO_ARCH" >&2
    TARGET_ARCH="$GO_ARCH"
fi

# Set Go cross-compilation environment
export GOOS=darwin
export GOARCH="$TARGET_ARCH"

# Set CGO flags for cross-compilation
if [ "$TARGET_ARCH" = "amd64" ]; then
    export CGO_CFLAGS="-arch x86_64"
    export CGO_LDFLAGS="-arch x86_64"
elif [ "$TARGET_ARCH" = "arm64" ]; then
    export CGO_CFLAGS="-arch arm64"
    export CGO_LDFLAGS="-arch arm64"
fi

# Prepare manta dependency
bash "${ROOT_DIR}/tools/prepare_manta.sh"

# Build the shared library
pushd "${ROOT_DIR}/go_wrapper" >/dev/null

go mod tidy

# Build shared library (dylib on macOS)
echo "Building with GOOS=$GOOS GOARCH=$GOARCH CGO_ENABLED=$CGO_ENABLED" >&2
go build -buildmode=c-shared -o libmanta_wrapper.so .

popd >/dev/null

# Copy to Python package
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.so" "${ROOT_DIR}/src/python_manta/"
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.h" "${ROOT_DIR}/src/python_manta/"

echo "macOS build preparation complete!" >&2
