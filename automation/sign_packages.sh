#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

if ! command -v gpg >/dev/null 2>&1; then
  echo "gpg is required but was not found"
  exit 1
fi

if [[ ! -d "${DIST_DIR}" ]]; then
  echo "dist directory not found; build packages first"
  exit 1
fi

KEY_ID="${1:-}"
SIG_ARGS=(--batch --yes --armor --detach-sign)
if [[ -n "${KEY_ID}" ]]; then
  SIG_ARGS+=(--local-user "${KEY_ID}")
fi

MANIFEST="${DIST_DIR}/SHA256SUMS"
FILE_LIST="$(mktemp)"
trap 'rm -f "${FILE_LIST}"' EXIT

find "${DIST_DIR}" -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.tar.gz" -o -name "PKGBUILD" \) | sort > "${FILE_LIST}"

if [[ ! -s "${FILE_LIST}" ]]; then
  echo "No package artifacts found to sign"
  exit 1
fi

: > "${MANIFEST}"
while IFS= read -r file; do
  sha256sum "${file}" >> "${MANIFEST}"
  gpg "${SIG_ARGS[@]}" --output "${file}.asc" "${file}"
  echo "Signed ${file}"
done < "${FILE_LIST}"

gpg "${SIG_ARGS[@]}" --output "${MANIFEST}.asc" "${MANIFEST}"
echo "Wrote ${MANIFEST} and ${MANIFEST}.asc"
