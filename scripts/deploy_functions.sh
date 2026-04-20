#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_azure_common.sh"

build_function_package() {
  local function_dir="$1"
  local artifact_name="$2"
  local staging_dir="${ROOT_DIR}/.artifacts/${artifact_name}"
  rm -rf "${staging_dir}"
  mkdir -p "${staging_dir}/.python_packages/lib/site-packages"
  "${PYTHON_CMD[@]}" -m pip install --upgrade pip >/dev/null
  "${PYTHON_CMD[@]}" -m pip install --target "${staging_dir}/.python_packages/lib/site-packages" "${ROOT_DIR}" >/dev/null
  cp "${function_dir}/function_app.py" "${staging_dir}/function_app.py"
  cp "${function_dir}/host.json" "${staging_dir}/host.json"
  cp -R "${ROOT_DIR}/src" "${staging_dir}/src"
  cp "${ROOT_DIR}/pyproject.toml" "${ROOT_DIR}/README.md" "${staging_dir}/"
  build_zip_from_directory "${staging_dir}" "${ROOT_DIR}/.artifacts/${artifact_name}.zip" >/dev/null
}

load_azure_env
azure_login_check
require_vars AZURE_RESOURCE_GROUP
load_bicep_outputs

build_function_package "${ROOT_DIR}/functions/indexer-function" "indexer-function"
build_function_package "${ROOT_DIR}/functions/custom-incidents-api-function" "custom-incidents-api-function"

az functionapp deployment source config-zip \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_INDEXER_FUNCTION_NAME}" \
  --src "${ROOT_DIR}/.artifacts/indexer-function.zip" >/dev/null

az functionapp deployment source config-zip \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_INCIDENTS_FUNCTION_NAME}" \
  --src "${ROOT_DIR}/.artifacts/custom-incidents-api-function.zip" >/dev/null

echo "Functions desplegadas: ${AZURE_INDEXER_FUNCTION_NAME}, ${AZURE_INCIDENTS_FUNCTION_NAME}"
