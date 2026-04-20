#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "${SCRIPT_DIR}/_azure_common.sh"

load_azure_env
azure_login_check
require_vars PROJECT_NAME ENVIRONMENT_NAME AZURE_LOCATION AZURE_RESOURCE_GROUP POSTGRES_ADMIN_USER POSTGRES_ADMIN_PASSWORD POSTGRES_DATABASE_NAME OPENAI_API_KEY CHAT_MODEL EMBEDDING_MODEL EMBEDDING_DIMENSIONS ADMIN_API_KEY APP_SHARED_SECRET MICROSOFT_APP_ID MICROSOFT_APP_PASSWORD

ALLOWED_ORIGINS_JSON="$(csv_to_json_array "${ALLOWED_ORIGINS:-}")"
ENABLE_APPLICATION_INSIGHTS="${ENABLE_APPLICATION_INSIGHTS:-true}"
DEPLOYMENT_NAME="${PROJECT_NAME}-${ENVIRONMENT_NAME}-infra"

az group create --name "${AZURE_RESOURCE_GROUP}" --location "${AZURE_LOCATION}" >/dev/null

az deployment group create \
  --name "${DEPLOYMENT_NAME}" \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --template-file "${ROOT_DIR}/infra/main.bicep" \
  --parameters \
    projectName="${PROJECT_NAME}" \
    environmentName="${ENVIRONMENT_NAME}" \
    location="${AZURE_LOCATION}" \
    postgresAdminUser="${POSTGRES_ADMIN_USER}" \
    postgresAdminPassword="${POSTGRES_ADMIN_PASSWORD}" \
    postgresDatabaseName="${POSTGRES_DATABASE_NAME}" \
    openAiApiKey="${OPENAI_API_KEY}" \
    chatModel="${CHAT_MODEL}" \
    embeddingModel="${EMBEDDING_MODEL}" \
    embeddingDimensions="${EMBEDDING_DIMENSIONS}" \
    adminApiKey="${ADMIN_API_KEY}" \
    appSharedSecret="${APP_SHARED_SECRET}" \
    microsoftAppId="${MICROSOFT_APP_ID}" \
    microsoftAppPassword="${MICROSOFT_APP_PASSWORD}" \
    allowedOrigins="${ALLOWED_ORIGINS_JSON}" \
    enableApplicationInsights="${ENABLE_APPLICATION_INSIGHTS}" >/dev/null

load_bicep_outputs
CLIENT_IP="$(current_public_ip)"
az postgres flexible-server firewall-rule create \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --name "${AZURE_POSTGRES_SERVER_NAME}" \
  --rule-name "local-client" \
  --start-ip-address "${CLIENT_IP}" \
  --end-ip-address "${CLIENT_IP}" >/dev/null

echo "Infra desplegada: ${AZURE_RESOURCE_GROUP}"
echo "Web App: ${AZURE_WEBAPP_NAME}"
echo "Indexer Function: ${AZURE_INDEXER_FUNCTION_NAME}"
echo "Incidents Function: ${AZURE_INCIDENTS_FUNCTION_NAME}"
echo "PostgreSQL: ${AZURE_POSTGRES_SERVER_NAME}"
