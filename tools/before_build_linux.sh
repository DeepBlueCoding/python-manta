#!/usr/bin/env bash
# Prepare Go toolchain, manta dependency, and build the shared library for wheels.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
GO_VERSION=${GO_VERSION:-1.21.5}
GO_INSTALL_DIR=${GO_INSTALL_DIR:-/opt/go}

ensure_tool() {
    local binary=$1
    local package=${2:-$1}
    if command -v "${binary}" >/dev/null 2>&1; then
        return 0
    fi
    if command -v yum >/dev/null 2>&1; then
        yum install -y "${package}"
    else
        echo "Required tool '${binary}' is not available and automatic installation is unsupported on this platform." >&2
        exit 1
    fi
}

ensure_tool git
ensure_tool curl

if ! command -v go >/dev/null 2>&1; then
    echo "Installing Go ${GO_VERSION}" >&2
    TEMP_ARCHIVE=$(mktemp)
    curl -sSL "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz" -o "${TEMP_ARCHIVE}"
    rm -rf "${GO_INSTALL_DIR}"
    tar -C "$(dirname "${GO_INSTALL_DIR}")" -xzf "${TEMP_ARCHIVE}"
    rm -f "${TEMP_ARCHIVE}"
    ln -sf "${GO_INSTALL_DIR}/bin/go" /usr/local/bin/go
else
    echo "Go already available: $(go version)" >&2
fi

export PATH="${GO_INSTALL_DIR}/bin:${PATH}"
export CGO_ENABLED=1

bash "${ROOT_DIR}/tools/prepare_manta.sh"

pushd "${ROOT_DIR}/go_wrapper" >/dev/null

# Ensure the local replace path stays valid during the build.
go mod tidy

go build -buildmode=c-shared -o libmanta_wrapper.so .

popd >/dev/null

cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.so" "${ROOT_DIR}/src/python_manta/"
cp "${ROOT_DIR}/go_wrapper/libmanta_wrapper.h" "${ROOT_DIR}/src/python_manta/"
