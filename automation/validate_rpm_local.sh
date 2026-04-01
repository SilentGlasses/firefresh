#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v rpmbuild >/dev/null 2>&1; then
  echo "[SKIP] rpmbuild is not installed. Install rpm-build to run local RPM validation."
  exit 0
fi

if ! command -v rpm >/dev/null 2>&1; then
  echo "[SKIP] rpm is not installed. Install rpm to inspect built RPM artifacts."
  exit 0
fi

cd "${ROOT_DIR}"
./automation/package_rpm.sh
bash ./automation/test_packages.sh