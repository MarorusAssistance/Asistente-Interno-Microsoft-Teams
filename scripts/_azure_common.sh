#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AZURE_ENV_FILE="${AZURE_ENV_FILE:-${ROOT_DIR}/.env.azure}"
DEPLOYMENT_NAME="${DEPLOYMENT_NAME:-${PROJECT_NAME:-internal-assistant}-${ENVIRONMENT_NAME:-demo}-infra}"
declare -a PYTHON_CMD=()

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

ensure_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Falta el comando requerido: $1"
}

resolve_python_cmd() {
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return
  fi
  if command -v py >/dev/null 2>&1; then
    PYTHON_CMD=(py -3)
    return
  fi
  fail "No se encontro Python en PATH"
}

load_azure_env() {
  if [[ -f "${AZURE_ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${AZURE_ENV_FILE}"
    set +a
  fi
}

require_vars() {
  local missing=()
  local name
  for name in "$@"; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("${name}")
    fi
  done
  if (( ${#missing[@]} > 0 )); then
    fail "Faltan variables requeridas: ${missing[*]}"
  fi
}

azure_login_check() {
  ensure_command az
  if ! az account show >/dev/null 2>&1; then
    fail "No hay sesion activa en Azure CLI. Ejecuta: az login"
  fi
  if [[ -n "${AZURE_SUBSCRIPTION_ID:-}" ]]; then
    az account set --subscription "${AZURE_SUBSCRIPTION_ID}" >/dev/null
  fi
}

csv_to_json_array() {
  local value="${1:-}"
  "${PYTHON_CMD[@]}" - "$value" <<'PY'
import json
import sys

items = [item.strip() for item in sys.argv[1].split(",") if item.strip()]
print(json.dumps(items))
PY
}

current_public_ip() {
  "${PYTHON_CMD[@]}" - <<'PY'
from urllib.request import urlopen

print(urlopen("https://api.ipify.org", timeout=10).read().decode("utf-8").strip())
PY
}

deployment_output() {
  local output_name="$1"
  az deployment group show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" \
    --query "properties.outputs.${output_name}.value" \
    -o tsv
}

load_bicep_outputs() {
  export AZURE_WEBAPP_NAME="$(deployment_output webAppName)"
  export AZURE_WEBAPP_HOSTNAME="$(deployment_output webAppHostname)"
  export AZURE_INDEXER_FUNCTION_NAME="$(deployment_output indexerFunctionName)"
  export AZURE_INDEXER_FUNCTION_HOSTNAME="$(deployment_output indexerFunctionHostname)"
  export AZURE_INCIDENTS_FUNCTION_NAME="$(deployment_output incidentsFunctionName)"
  export AZURE_INCIDENTS_FUNCTION_HOSTNAME="$(deployment_output incidentsFunctionHostname)"
  export AZURE_POSTGRES_SERVER_NAME="$(deployment_output postgresServerName)"
  export AZURE_STORAGE_ACCOUNT_NAME="$(deployment_output storageAccountName)"
  export AZURE_BOT_RESOURCE_NAME="$(deployment_output botName)"
  export APPLICATIONINSIGHTS_CONNECTION_STRING="${APPLICATIONINSIGHTS_CONNECTION_STRING:-$(deployment_output applicationInsightsConnectionString)}"
}

build_database_url() {
  require_vars AZURE_POSTGRES_SERVER_NAME POSTGRES_DATABASE_NAME POSTGRES_ADMIN_USER POSTGRES_ADMIN_PASSWORD
  "${PYTHON_CMD[@]}" - "${AZURE_POSTGRES_SERVER_NAME}" "${POSTGRES_DATABASE_NAME}" "${POSTGRES_ADMIN_USER}" "${POSTGRES_ADMIN_PASSWORD}" <<'PY'
import sys
from urllib.parse import quote_plus

server_name = sys.argv[1]
database_name = sys.argv[2]
admin_user = sys.argv[3]
password = quote_plus(sys.argv[4])

print(
    f"postgresql+psycopg://{admin_user}:{password}"
    f"@{server_name}.postgres.database.azure.com:5432/{database_name}?sslmode=require"
)
PY
}

build_zip_from_directory() {
  local source_dir="$1"
  local output_file="$2"
  "${PYTHON_CMD[@]}" - "${source_dir}" "${output_file}" <<'PY'
from pathlib import Path
import sys
import zipfile

source = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve()
target.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in source.rglob("*"):
        if path.is_file():
            archive.write(path, path.relative_to(source))
print(target)
PY
}

resolve_python_cmd
