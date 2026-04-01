#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
EXPECTED_REPO_URL="https://github.com/SilentGlasses/firefresh"
EXPECTED_MAINTAINER_EMAIL="silentglasses@proton.me"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

pass() {
  echo "[PASS] $*"
}

if [[ ! -d "${DIST_DIR}" ]]; then
  fail "dist directory not found; build packages first"
fi

# Test Debian package contents if present.
shopt -s nullglob
DEBS=("${DIST_DIR}"/*.deb)
if (( ${#DEBS[@]} > 0 )); then
  if ! command -v dpkg-deb >/dev/null 2>&1; then
    fail "dpkg-deb required to test .deb artifacts"
  fi

  for deb in "${DEBS[@]}"; do
    dpkg-deb -I "${deb}" >/dev/null || fail "invalid deb control metadata: ${deb}"
    DEB_PACKAGE="$(dpkg-deb -f "${deb}" Package)"
    DEB_VERSION="$(dpkg-deb -f "${deb}" Version)"
    DEB_MAINTAINER="$(dpkg-deb -f "${deb}" Maintainer)"
    DEB_DEPENDS="$(dpkg-deb -f "${deb}" Depends)"

    [[ "${DEB_PACKAGE}" == "firefox-installer" ]] || fail "unexpected deb package name in ${deb}: ${DEB_PACKAGE}"
    [[ -n "${DEB_VERSION}" ]] || fail "missing deb version in ${deb}"
    [[ "${DEB_MAINTAINER}" == *"${EXPECTED_MAINTAINER_EMAIL}"* ]] || fail "unexpected deb maintainer in ${deb}: ${DEB_MAINTAINER}"
    [[ "${DEB_MAINTAINER}" != *"example.invalid"* ]] || fail "placeholder maintainer email found in ${deb}"
    [[ "${DEB_DEPENDS}" == *"python3"* ]] || fail "python3 dependency missing in ${deb}"

    dpkg-deb -c "${deb}" | grep -q "./usr/bin/firefox-installer" || fail "launcher missing in ${deb}"
    dpkg-deb -c "${deb}" | grep -q "./usr/lib/firefox-installer/src/firefox_installer_app/cli.py" || fail "cli module missing in ${deb}"
    pass "validated ${deb}"
  done
else
  echo "[INFO] no .deb artifacts found"
fi

# Test RPM package contents if present.
RPMS=("${DIST_DIR}"/*.rpm)
if (( ${#RPMS[@]} > 0 )); then
  if ! command -v rpm >/dev/null 2>&1; then
    fail "rpm command required to test .rpm artifacts"
  fi

  for rpm_pkg in "${RPMS[@]}"; do
    RPM_NAME="$(rpm -qp --qf '%{NAME}' "${rpm_pkg}")"
    RPM_VERSION="$(rpm -qp --qf '%{VERSION}' "${rpm_pkg}")"
    RPM_URL="$(rpm -qp --qf '%{URL}' "${rpm_pkg}")"

    [[ "${RPM_NAME}" == "firefox-installer" ]] || fail "unexpected rpm package name in ${rpm_pkg}: ${RPM_NAME}"
    [[ -n "${RPM_VERSION}" ]] || fail "missing rpm version in ${rpm_pkg}"
    [[ "${RPM_URL}" == "${EXPECTED_REPO_URL}" ]] || fail "unexpected rpm URL in ${rpm_pkg}: ${RPM_URL}"
    [[ "${RPM_URL}" != *"example.invalid"* ]] || fail "placeholder URL found in ${rpm_pkg}"

    rpm -qpl "${rpm_pkg}" | grep -q "/usr/bin/firefox-installer" || fail "launcher missing in ${rpm_pkg}"
    rpm -qpl "${rpm_pkg}" | grep -q "/usr/lib/firefox-installer/src/firefox_installer_app/cli.py" || fail "cli module missing in ${rpm_pkg}"
    pass "validated ${rpm_pkg}"
  done
else
  echo "[INFO] no .rpm artifacts found"
fi

# Test AUR bundle if present.
AUR_PKG="${DIST_DIR}/aur/PKGBUILD"
AUR_TAR=("${DIST_DIR}/aur/firefox-installer-"*.tar.gz)
if [[ -f "${AUR_PKG}" && ${#AUR_TAR[@]} -eq 0 ]]; then
  fail "PKGBUILD found but no AUR tarball found"
fi

if [[ ! -f "${AUR_PKG}" && ${#AUR_TAR[@]} -gt 0 ]]; then
  fail "AUR tarball found but PKGBUILD is missing"
fi

if [[ -f "${AUR_PKG}" && ${#AUR_TAR[@]} -gt 1 ]]; then
  fail "multiple AUR tarballs found; expected exactly one"
fi

if [[ -f "${AUR_PKG}" && ${#AUR_TAR[@]} -eq 1 ]]; then
  SHA_ACTUAL="$(sha256sum "${AUR_TAR[0]}" | awk '{print $1}')"
  SHA_DECLARED="$(grep "^sha256sums=" "${AUR_PKG}" | sed -E "s/.*'([a-f0-9]{64})'.*/\1/")"
  PKGVER_DECLARED="$(grep "^pkgver=" "${AUR_PKG}" | sed -E 's/^pkgver=//')"
  URL_DECLARED="$(grep '^url=' "${AUR_PKG}" | sed -E 's/^url="([^"]+)"/\1/')"
  TARBALL_VERSION="$(basename "${AUR_TAR[0]}" | sed -E 's/^firefox-installer-(.+)\.tar\.gz$/\1/')"

  [[ -n "${SHA_DECLARED}" ]] || fail "missing sha256 in PKGBUILD"
  [[ "${SHA_ACTUAL}" == "${SHA_DECLARED}" ]] || fail "sha256 mismatch in PKGBUILD"
  grep -q "pkgname=firefox-installer" "${AUR_PKG}" || fail "invalid PKGBUILD pkgname"
  [[ "${PKGVER_DECLARED}" == "${TARBALL_VERSION}" ]] || fail "PKGBUILD pkgver does not match tarball version"
  [[ "${URL_DECLARED}" == "${EXPECTED_REPO_URL}" ]] || fail "unexpected PKGBUILD URL: ${URL_DECLARED}"
  ! grep -q "example.invalid" "${AUR_PKG}" || fail "placeholder URL found in PKGBUILD"
  pass "validated AUR bundle"
else
  echo "[INFO] no AUR artifacts found"
fi

pass "artifact smoke tests completed"
