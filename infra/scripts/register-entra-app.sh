#!/usr/bin/env bash
#
# register-entra-app.sh — Register an Entra ID app for the DocTalk API
#
# Usage:
#   ./infra/scripts/register-entra-app.sh
#
# Prerequisites:
#   - Azure CLI authenticated (az login)
#   - Application Administrator or Global Administrator role
#
# Outputs ENTRA_CLIENT_ID and ENTRA_TENANT_ID for use in project config.
#
set -euo pipefail

APP_DISPLAY_NAME="${ENTRA_APP_NAME:-DocTalk API}"
REDIRECT_URI="https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect"
SCOPE_NAME="Podcasts.ReadWrite"

echo "==> Registering Entra ID application: ${APP_DISPLAY_NAME}"

# Generate a UUID for the OAuth2 permission scope
SCOPE_ID=$(python3 -c "import uuid; print(uuid.uuid4())" 2>/dev/null \
           || uuidgen \
           || cat /proc/sys/kernel/random/uuid)

# Build the API permissions body
API_BODY=$(cat <<EOF
{
  "requestedAccessTokenVersion": 2,
  "oauth2PermissionScopes": [
    {
      "id": "${SCOPE_ID}",
      "adminConsentDescription": "Allows the app to generate and manage podcasts on behalf of the user",
      "adminConsentDisplayName": "Read and write podcasts",
      "userConsentDescription": "Allows DocTalk to generate and manage podcasts for you",
      "userConsentDisplayName": "Read and write your podcasts",
      "isEnabled": true,
      "type": "User",
      "value": "${SCOPE_NAME}"
    }
  ]
}
EOF
)

# Create the app registration (single-tenant, web redirect URI)
APP_ID=$(az ad app create \
  --display-name "${APP_DISPLAY_NAME}" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "${REDIRECT_URI}" \
  --enable-access-token-issuance false \
  --enable-id-token-issuance false \
  --query "appId" \
  --output tsv)

echo "==> App registered. Client ID: ${APP_ID}"

# Set the Application ID URI (required before scopes work)
echo "==> Setting Application ID URI: api://${APP_ID}"
az ad app update \
  --id "${APP_ID}" \
  --identifier-uris "api://${APP_ID}"

# Configure API settings: token version + scopes
echo "==> Configuring API scope: api://${APP_ID}/${SCOPE_NAME}"
az ad app update \
  --id "${APP_ID}" \
  --set "api=$(echo "${API_BODY}" | tr -d '\n')"

# Retrieve tenant ID
TENANT_ID=$(az account show --query "tenantId" --output tsv)

echo ""
echo "============================================"
echo " Entra ID App Registration Complete"
echo "============================================"
echo ""
echo " App Name:        ${APP_DISPLAY_NAME}"
echo " ENTRA_CLIENT_ID: ${APP_ID}"
echo " ENTRA_TENANT_ID: ${TENANT_ID}"
echo " API Scope:       api://${APP_ID}/${SCOPE_NAME}"
echo " Redirect URI:    ${REDIRECT_URI}"
echo " Token Version:   v2.0"
echo ""
echo "Add these to your .env.dev (do NOT commit):"
echo ""
echo "  ENTRA_CLIENT_ID=${APP_ID}"
echo "  ENTRA_TENANT_ID=${TENANT_ID}"
echo ""
