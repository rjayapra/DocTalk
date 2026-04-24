# Tank Agent History

## 2026-04-24 — UI Task Breakdown Complete
A comprehensive 39-task UI build plan has been created spanning 3 phases. Tank has been assigned infrastructure and optimization tasks to support the UI implementation. See `.squad/decisions/decisions.md` for full task manifest and assignments.

### ARCHITECTURE.md M365 Copilot Agent Update
- Replaced all Bot Framework references (sections 3, 4, 6.3, 7, 8, 11, 12, 14) with M365 Copilot declarative agent + API plugin approach
- Updated diagrams to show Copilot orchestrator flow instead of direct Bot Framework messaging
- Removed Azure Bot Service from resource architecture and cost estimates (no longer needed)
- Section 6.3 now documents the actual `appPackage/` file structure: `manifest.json`, `declarativeAgent.json`, `doctalk-plugin.json`, `openapi.yaml`
- Section 8 now shows Copilot conversation starters and Adaptive Card rendering UX

## Learnings

### Teams Toolkit Project Structure
- `teamsapp.yml` / `teamsapp.local.yml` use v1.7 schema with provision → deploy → publish lifecycle
- Manifest at `appPackage/manifest.json` uses Teams schema v1.19 for M365 Copilot declarative agent support
- `copilotAgents.declarativeAgents` array in manifest links to `declarativeAgent.json` (agent definition file)
- `validDomains` must include the ACA API hostname for API plugin calls
- `webApplicationInfo` references Entra app ID for OAuth — uses `${{ENTRA_APP_ID}}` placeholder syntax
- Environment variables live in `env/.env.dev` with Teams Toolkit `${{VAR}}` interpolation syntax
- Icon requirements: `color.png` = 192×192 full color, `outline.png` = 32×32 white-on-transparent
- API URL: `https://ca-doctalk-api-m4ydxz.thankfulwave-bd3e8cef.eastus2.azurecontainerapps.io`

### Key File Paths
- `teamsapp.yml` — main Teams Toolkit config
- `teamsapp.local.yml` — local sideload dev config
- `appPackage/manifest.json` — Teams app manifest
- `appPackage/color.png` — 192×192 placeholder icon (needs real artwork)
- `appPackage/outline.png` — 32×32 placeholder icon (needs real artwork)
- `appPackage/ICON-REQUIREMENTS.md` — design specs for replacement icons
- `env/.env.dev` — dev environment variables

## Learnings

### Entra ID App Registration (Task #12)
- Created `infra/entra-app-registration.md` runbook covering both automated and manual portal registration paths.
- Created `infra/scripts/register-entra-app.sh` that uses `az ad app create` with single-tenant audience, Teams redirect URI, `Podcasts.ReadWrite` scope, and `accessTokenAcceptedVersion: 2`.
- Client ID and tenant ID are output as env vars (`ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`) — never hardcoded.
- The Teams OAuth redirect URI must be exactly `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`.
- `az ad app update --set "api=..."` is the way to configure both token version and scopes in one shot.

### Entra ID Bicep Integration (Task #12 — azd up)
- Microsoft Graph Bicep (`extension microsoftGraphV1`) is GA and uses `Microsoft.Graph/applications@v1.0`.
- The `uniqueName` property is required for idempotent Graph resource deployments.
- `appId` is auto-generated — you cannot set `identifierUris` to `api://{appId}` in the same Bicep resource (circular reference). Must use a postprovision hook.
- `signInAudience` uses `AzureADMyOrg` (not `AzureADandPersonalMicrosoftAccount`).
- `newGuid()` works for generating scope IDs in Bicep — only evaluated once per deployment.
- The `extension microsoftGraphV1` declaration must appear in both the module file AND the parent `main.bicep` when main.bicep is subscription-scoped and the module is resource-group scoped.
- AZD automatically populates env vars from Bicep outputs, so `ENTRA_APP_ID` output flows to postprovision hooks.

### Key File Paths (Entra Bicep)
- `infra/modules/entra-app.bicep` — Microsoft Graph Bicep module for Entra app registration
- `infra/main.bicep` — wires entra-app module, outputs ENTRA_APP_ID and ENTRA_TENANT_ID
- `azure.yaml` — postprovision hook sets Application ID URI via `az ad app update`

## 2025-01-08 — Teams Toolkit v6.9 Schema Fixes + OAuth Removal

### Issue Resolution
- Fixed `InvalidYamlSchemaError` in `teamsapp.yml` by removing invalid `deploy` section
- The `devTool/install` action with `devCert: trust: true` is ONLY valid in `teamsapp.local.yml` for local dev, NOT in the main `teamsapp.yml`
- For declarative Copilot agent + API plugin, there is NO backend to deploy via TTK — backend is already deployed to Azure Container Apps via `azd up`
- TTK workflow is ONLY for registering the Teams app, packaging the manifest, and sideloading

### OAuth Removal for Wave 1
- Removed OAuth/Entra configuration since no downstream OBO token exchange is needed for wave 1
- Stripped `webApplicationInfo` section from `manifest.json` (it referenced `ENTRA_APP_ID`)
- Changed plugin auth from `OAuthPluginVault` to `"none"` in `doctalk-plugin.json`
- Removed OAuth2 `securitySchemes` and `security` array from `openapi.yaml`
- Updated `env/.env.dev` with new deployed API URL: `https://ca-doctalk-api-m4ydxz.thankfulwave-bd3e8cef.eastus2.azurecontainerapps.io`
- Removed `ENTRA_APP_ID` and `ENTRA_TENANT_ID` lines from `env/.env.dev`
- Updated `docs/SMOKE-TEST-CHECKLIST.md` to reflect that OAuth/Entra setup is not needed for wave 1

## Learnings

### Teams Toolkit v6.9 Schema Validation
- `teamsapp.yml` (main config) should contain ONLY: `provision` and `publish` sections
- `deploy` section is ONLY valid in `teamsapp.local.yml` for local dev workflows (e.g., dev cert trust)
- When backend is already deployed (via `azd up` to ACA), TTK does NOT deploy it — TTK only provisions Teams app registration
- Schema errors manifest as `InvalidYamlSchemaError` with the file path — check for sections that belong in `.local.yml` instead

### Declarative Copilot Agent Auth Configuration
- Plugin auth type `"none"` is valid when API doesn't require authentication
- When auth is `"none"`, remove `webApplicationInfo` from `manifest.json`
- When auth is `"none"`, remove `security` and `components.securitySchemes` from OpenAPI spec
- OpenAPI spec `servers[0].url` must match actual deployed API URL (not placeholder)
