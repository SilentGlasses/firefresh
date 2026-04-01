#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist"
PKG_NAME="firefox-installer"

VERSION="$(python3 -c "import sys; sys.path.insert(0, '${ROOT_DIR}/src'); from firefox_installer_app import __version__; print(__version__)")"
ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"

BUILD_DIR="$(mktemp -d)"
PKG_ROOT="${BUILD_DIR}/${PKG_NAME}_${VERSION}_${ARCH}"
trap 'rm -rf "${BUILD_DIR}"' EXIT

mkdir -p "${OUT_DIR}" "${PKG_ROOT}/DEBIAN" "${PKG_ROOT}/usr/lib/firefox-installer/src/firefox_installer_app" "${PKG_ROOT}/usr/bin"

cat > "${PKG_ROOT}/DEBIAN/control" <<EOF
Package: ${PKG_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: silentglasses <silentglasses@proton.me>
Depends: python3 (>= 3.8)
Description: Distro-aware Firefox installer for Linux
 Installs the firefox-installer CLI for managing Firefox source installs.
EOF

cp "${ROOT_DIR}/src/firefox_installer_app/"*.py "${PKG_ROOT}/usr/lib/firefox-installer/src/firefox_installer_app/"
install -m 0755 "${ROOT_DIR}/packaging/common/firefox-installer-launcher" "${PKG_ROOT}/usr/bin/firefox-installer"

dpkg-deb --build "${PKG_ROOT}" "${OUT_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb" >/dev/null

echo "Created ${OUT_DIR}/${PKG_NAME}_${VERSION}_${ARCH}.deb"
