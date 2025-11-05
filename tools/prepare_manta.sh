#!/usr/bin/env bash
# Ensure the dotabuff/manta dependency is available locally for Go builds.

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
WRAPPER_DIR="${ROOT_DIR}/go_wrapper"
MANTA_DIR=${MANTA_DIR:-"${WRAPPER_DIR}/manta"}
MANTA_REPO=${MANTA_REPO:-"https://github.com/dotabuff/manta.git"}
MANTA_REF=${MANTA_REF:-main}

if [[ -d "${MANTA_DIR}/.git" ]]; then
    echo "Updating manta checkout at ${MANTA_DIR}" >&2
    git -C "${MANTA_DIR}" fetch origin "${MANTA_REF}" --depth 1
    git -C "${MANTA_DIR}" reset --hard "FETCH_HEAD"
else
    echo "Cloning manta (${MANTA_REF}) into ${MANTA_DIR}" >&2
    rm -rf "${MANTA_DIR}"
    git clone --depth 1 --branch "${MANTA_REF}" "${MANTA_REPO}" "${MANTA_DIR}"
fi

MANTA_COMMIT=$(git -C "${MANTA_DIR}" rev-parse HEAD)
echo "Using manta commit ${MANTA_COMMIT}" >&2

printf '%s
' "${MANTA_COMMIT}" > "${WRAPPER_DIR}/manta.commit"
