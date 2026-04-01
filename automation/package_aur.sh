#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist/aur"
PKG_NAME="firefox-installer"

VERSION="$(python3 -c "import sys; sys.path.insert(0, '${ROOT_DIR}/src'); from firefox_installer_app import __version__; print(__version__)")"
SRC_DIR="$(mktemp -d)"
trap 'rm -rf "${SRC_DIR}"' EXIT

mkdir -p "${OUT_DIR}"
WORK_DIR="${SRC_DIR}/${PKG_NAME}-${VERSION}"
mkdir -p "${WORK_DIR}"

cp -r "${ROOT_DIR}/src" "${WORK_DIR}/"
cp -r "${ROOT_DIR}/packaging" "${WORK_DIR}/"
cp "${ROOT_DIR}/README.md" "${ROOT_DIR}/LICENSE" "${WORK_DIR}/"

TARBALL="${OUT_DIR}/${PKG_NAME}-${VERSION}.tar.gz"
tar -C "${SRC_DIR}" -czf "${TARBALL}" "${PKG_NAME}-${VERSION}"
SHA256="$(sha256sum "${TARBALL}" | awk '{print $1}')"

sed -e "s/@VERSION@/${VERSION}/g" -e "s/@SHA256@/${SHA256}/g" "${ROOT_DIR}/packaging/aur/PKGBUILD.in" > "${OUT_DIR}/PKGBUILD"

echo "Created ${TARBALL}"
echo "Created ${OUT_DIR}/PKGBUILD"
