# Tank Agent History

## 2026-04-24 — UI Task Breakdown Complete
A comprehensive 39-task UI build plan has been created spanning 3 phases. Tank has been assigned infrastructure and optimization tasks to support the UI implementation. See `.squad/decisions/decisions.md` for full task manifest and assignments.

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
