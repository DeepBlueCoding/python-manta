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

# Prepare manta dependency
bash "${ROOT_DIR}/tools/prepare_manta.sh"

# Build the shared library
pushd "${ROOT_DIR}/go_wrapper" >/dev/null

go mod tidy

# Build shared library (dylib on macOS)
go build -buildmode=c-shared -o libmanta_wrapper.so .

popd >/dev/null

# Copy to Python package
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.so" "${ROOT_DIR}/src/python_manta/"
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.h" "${ROOT_DIR}/src/python_manta/"

echo "macOS build preparation complete!" >&2
