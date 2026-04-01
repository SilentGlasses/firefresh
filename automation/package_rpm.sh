#!/usr/bin/env bash
set -euo pipefail

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "rpmbuild is required but was not found."
  echo "Install rpm-build and run this command again."
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist"
RPMROOT="$(mktemp -d)"
trap 'rm -rf "${RPMROOT}"' EXIT

VERSION="$(python3 -c "import sys; sys.path.insert(0, '${ROOT_DIR}/src'); from firefox_installer_app import __version__; print(__version__)")"
PKG_NAME="firefox-installer"
SRC_BASENAME="${PKG_NAME}-${VERSION}"

mkdir -p "${OUT_DIR}" "${RPMROOT}"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

STAGE_DIR="$(mktemp -d)"
trap 'rm -rf "${RPMROOT}" "${STAGE_DIR}"' EXIT
mkdir -p "${STAGE_DIR}/${SRC_BASENAME}"

cp -r "${ROOT_DIR}/src" "${STAGE_DIR}/${SRC_BASENAME}/"
cp -r "${ROOT_DIR}/packaging" "${STAGE_DIR}/${SRC_BASENAME}/"
cp "${ROOT_DIR}/README.md" "${ROOT_DIR}/LICENSE" "${STAGE_DIR}/${SRC_BASENAME}/"

tar -C "${STAGE_DIR}" -czf "${RPMROOT}/SOURCES/${SRC_BASENAME}.tar.gz" "${SRC_BASENAME}"
sed "s/@VERSION@/${VERSION}/g" "${ROOT_DIR}/packaging/rpm/firefox-installer.spec.in" > "${RPMROOT}/SPECS/firefox-installer.spec"

rpmbuild -bb "${RPMROOT}/SPECS/firefox-installer.spec" --define "_topdir ${RPMROOT}" >/dev/null
find "${RPMROOT}/RPMS" -name "*.rpm" -exec cp {} "${OUT_DIR}/" \;

echo "Created RPM package(s) in ${OUT_DIR}"
