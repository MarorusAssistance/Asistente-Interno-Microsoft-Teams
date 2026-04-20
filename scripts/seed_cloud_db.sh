#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_azure_common.sh"

load_azure_env
azure_login_check
load_bicep_outputs
export DATABASE_URL="$(build_database_url)"
export APP_ENV="${APP_ENV:-demo}"

"${PYTHON_CMD[@]}" -m uv run python "${ROOT_DIR}/scripts/validate_seed_data.py"
"${PYTHON_CMD[@]}" -m uv run python "${ROOT_DIR}/scripts/seed_db.py"
