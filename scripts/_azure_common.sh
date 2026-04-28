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

native_path() {
  local path="$1"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -aw "${path}"
    return
  fi
  if [[ "${path}" =~ ^/mnt/([a-zA-Z])/(.*)$ ]]; then
    local drive="${BASH_REMATCH[1]}"
    local rest="${BASH_REMATCH[2]}"
    rest="${rest//\//\\}"
    printf '%s:\\%s\n' "${drive^}" "${rest}"
    return
  fi
  printf '%s\n' "${path}"
}

bash_path() {
  local path="$1"
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "${path}"
    return
  fi
  if [[ "${path}" =~ ^([a-zA-Z]):\\(.*)$ ]]; then
    local drive="${BASH_REMATCH[1],,}"
    local rest="${BASH_REMATCH[2]}"
    rest="${rest//\\//}"
    if [[ -d "/mnt/${drive}" ]]; then
      printf '/mnt/%s/%s\n' "${drive}" "${rest}"
    else
      printf '/%s/%s\n' "${drive}" "${rest}"
    fi
    return
  fi
  printf '%s\n' "${path}"
}

resolve_python_cmd() {
  if command -v where.exe >/dev/null 2>&1; then
    local windows_python=""
    windows_python="$(where.exe python.exe 2>/dev/null | tr -d '\r' | head -n 1 || true)"
    if [[ -n "${windows_python}" ]]; then
      PYTHON_CMD=("$(bash_path "${windows_python}")")
      return
    fi
    local windows_py=""
    windows_py="$(where.exe py.exe 2>/dev/null | tr -d '\r' | head -n 1 || true)"
    if [[ -n "${windows_py}" ]]; then
      PYTHON_CMD=("$(bash_path "${windows_py}")" -3)
      return
    fi
  fi
  if command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return
  fi
  if command -v py >/dev/null 2>&1; then
    PYTHON_CMD=(py -3)
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
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
    -o tsv | tr -d '\r\n'
}

assert_deployment_exists() {
  az deployment group show \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${DEPLOYMENT_NAME}" >/dev/null 2>&1 || fail "No existe el deployment '${DEPLOYMENT_NAME}'. Revisa primero el error de deploy_infra.sh y no ejecutes los pasos siguientes hasta que termine bien."
}

load_bicep_outputs() {
  assert_deployment_exists
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

webapp_appsetting() {
  local setting_name="$1"
  az webapp config appsettings list \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${AZURE_WEBAPP_NAME}" \
    --query "[?name=='${setting_name}'].value | [0]" \
    -o tsv | tr -d '\r\n'
}

build_database_url() {
  require_vars AZURE_POSTGRES_SERVER_NAME POSTGRES_DATABASE_NAME POSTGRES_ADMIN_USER POSTGRES_ADMIN_PASSWORD
  "${PYTHON_CMD[@]}" - "${AZURE_POSTGRES_SERVER_NAME}" "${POSTGRES_DATABASE_NAME}" "${POSTGRES_ADMIN_USER}" "${POSTGRES_ADMIN_PASSWORD}" <<'PY' | tr -d '\r\n'
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
  local source_native
  local output_native
  source_native="$(native_path "${source_dir}")"
  output_native="$(native_path "${output_file}")"
  "${PYTHON_CMD[@]}" - "${source_native}" "${output_native}" <<'PY'
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

run_uv_python_script() {
  local script_path="$1"
  shift || true
  local -a env_pairs=("$@")

  if command -v powershell.exe >/dev/null 2>&1 && [[ "${PYTHON_CMD[0]}" =~ ^/mnt/[a-zA-Z]/ ]]; then
    local python_native
    local script_native
    local ps_command
    local pair
    local name
    local value

    python_native="$(native_path "${PYTHON_CMD[0]}")"
    script_native="$(native_path "${script_path}")"
    ps_command="\$ErrorActionPreference='Stop';"
    for pair in "${env_pairs[@]}"; do
      name="${pair%%=*}"
      value="${pair#*=}"
      value="${value//\'/''}"
      ps_command+="\$env:${name}='${value}';"
    done
    ps_command+="& '${python_native}' -m uv run python '${script_native}'"
    powershell.exe -NoProfile -Command "${ps_command}"
    return
  fi

  local -a env_command=(env)
  local pair
  for pair in "${env_pairs[@]}"; do
    env_command+=("${pair}")
  done
  "${env_command[@]}" "${PYTHON_CMD[@]}" -m uv run python "${script_path}"
}

resolve_python_cmd
