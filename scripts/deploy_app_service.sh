#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_azure_common.sh"

build_webapp_package() {
  local staging_dir="${ROOT_DIR}/.artifacts/app-service"
  rm -rf "${staging_dir}"
  mkdir -p "${staging_dir}/.python_packages/lib/site-packages"
  "${PYTHON_CMD[@]}" -m pip install --upgrade pip >/dev/null
  "${PYTHON_CMD[@]}" -m pip install --target "${staging_dir}/.python_packages/lib/site-packages" "${ROOT_DIR}" >/dev/null
  cp -R "${ROOT_DIR}/app-service" "${staging_dir}/app-service"
  cp -R "${ROOT_DIR}/src" "${staging_dir}/src"
  cp "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/README.md" "${staging_dir}/"
  build_zip_from_directory "${staging_dir}" "${ROOT_DIR}/.artifacts/app-service.zip" >/dev/null
}

load_azure_env
azure_login_check
require_vars AZURE_RESOURCE_GROUP
load_bicep_outputs
build_webapp_package

az webapp deploy \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_WEBAPP_NAME}" \
  --src-path "${ROOT_DIR}/.artifacts/app-service.zip" \
  --type zip \
  --clean true \
  --restart true >/dev/null

echo "App Service desplegado: ${AZURE_WEBAPP_NAME}"
