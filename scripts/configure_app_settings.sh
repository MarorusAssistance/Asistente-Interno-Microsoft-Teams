#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_azure_common.sh"

load_azure_env
azure_login_check
require_vars PROJECT_NAME ENVIRONMENT_NAME AZURE_RESOURCE_GROUP POSTGRES_ADMIN_USER POSTGRES_ADMIN_PASSWORD POSTGRES_DATABASE_NAME OPENAI_API_KEY CHAT_MODEL EMBEDDING_MODEL EMBEDDING_DIMENSIONS ADMIN_API_KEY APP_SHARED_SECRET MICROSOFT_APP_ID MICROSOFT_APP_PASSWORD
load_bicep_outputs

DATABASE_URL="$(build_database_url)"
BOT_ENDPOINT="${BOT_ENDPOINT:-https://${AZURE_WEBAPP_HOSTNAME}/api/messages}"
CUSTOM_INCIDENTS_API_BASE_URL="${CUSTOM_INCIDENTS_API_BASE_URL:-https://${AZURE_INCIDENTS_FUNCTION_HOSTNAME}/api}"
INDEXER_API_BASE_URL="${INDEXER_API_BASE_URL:-https://${AZURE_INDEXER_FUNCTION_HOSTNAME}/api}"
DEFAULT_ALLOWED_ORIGINS="https://teams.microsoft.com,https://${AZURE_WEBAPP_HOSTNAME}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-${DEFAULT_ALLOWED_ORIGINS}}"
APP_ENV="${APP_ENV:-demo}"
APP_NAME="${APP_NAME:-internal-assistant-mvp}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"

az webapp config appsettings set \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_WEBAPP_NAME}" \
  --settings \
    APP_ENV="${APP_ENV}" \
    APP_NAME="${APP_NAME}" \
    DATABASE_URL="${DATABASE_URL}" \
    LLM_PROVIDER="${LLM_PROVIDER:-openai}" \
    EMBEDDINGS_PROVIDER="${EMBEDDINGS_PROVIDER:-openai}" \
    OPENAI_API_KEY="${OPENAI_API_KEY}" \
    CHAT_MODEL="${CHAT_MODEL}" \
    EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
    EMBEDDING_DIMENSIONS="${EMBEDDING_DIMENSIONS}" \
    ADMIN_API_KEY="${ADMIN_API_KEY}" \
    APP_SHARED_SECRET="${APP_SHARED_SECRET}" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="${APPLICATIONINSIGHTS_CONNECTION_STRING:-}" \
    ALLOWED_ORIGINS="${ALLOWED_ORIGINS}" \
    BOT_ENDPOINT="${BOT_ENDPOINT}" \
    CUSTOM_INCIDENTS_API_BASE_URL="${CUSTOM_INCIDENTS_API_BASE_URL}" \
    INDEXER_API_BASE_URL="${INDEXER_API_BASE_URL}" \
    MICROSOFT_APP_ID="${MICROSOFT_APP_ID}" \
    MICROSOFT_APP_PASSWORD="${MICROSOFT_APP_PASSWORD}" \
    TEAMS_APP_ID="${TEAMS_APP_ID:-}" \
    LOG_LEVEL="${LOG_LEVEL}" \
    PYTHONPATH="/home/site/wwwroot:/home/site/wwwroot/src:/home/site/wwwroot/.python_packages/lib/site-packages" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="false" \
    WEBSITE_RUN_FROM_PACKAGE="1" >/dev/null

az webapp config set \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_WEBAPP_NAME}" \
  --startup-file "gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:\$PORT --timeout 600 --access-logfile '-' --error-logfile '-' --chdir app-service main:app" >/dev/null

for function_app in "${AZURE_INDEXER_FUNCTION_NAME}" "${AZURE_INCIDENTS_FUNCTION_NAME}"; do
  az functionapp config appsettings set \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --name "${function_app}" \
    --settings \
      APP_ENV="${APP_ENV}" \
      APP_NAME="${APP_NAME}" \
      DATABASE_URL="${DATABASE_URL}" \
      LLM_PROVIDER="${LLM_PROVIDER:-openai}" \
      EMBEDDINGS_PROVIDER="${EMBEDDINGS_PROVIDER:-openai}" \
      OPENAI_API_KEY="${OPENAI_API_KEY}" \
      CHAT_MODEL="${CHAT_MODEL}" \
      EMBEDDING_MODEL="${EMBEDDING_MODEL}" \
      EMBEDDING_DIMENSIONS="${EMBEDDING_DIMENSIONS}" \
      ADMIN_API_KEY="${ADMIN_API_KEY}" \
      APP_SHARED_SECRET="${APP_SHARED_SECRET}" \
      APPLICATIONINSIGHTS_CONNECTION_STRING="${APPLICATIONINSIGHTS_CONNECTION_STRING:-}" \
      CUSTOM_INCIDENTS_API_BASE_URL="${CUSTOM_INCIDENTS_API_BASE_URL}" \
      INDEXER_API_BASE_URL="${INDEXER_API_BASE_URL}" \
      LOG_LEVEL="${LOG_LEVEL}" \
      PYTHONPATH="/home/site/wwwroot:/home/site/wwwroot/src:/home/site/wwwroot/.python_packages/lib/site-packages" \
      SCM_DO_BUILD_DURING_DEPLOYMENT="false" \
      WEBSITE_RUN_FROM_PACKAGE="1" >/dev/null
done

echo "App settings configuradas"
