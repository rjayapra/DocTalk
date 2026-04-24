# Entra ID App Registration — DocTalk API

> Runbook for registering the Entra ID application that enables OAuth 2.0 authentication
> between Microsoft 365 Copilot (API plugin) and the DocTalk API.

## Prerequisites

- Azure CLI (`az`) installed and authenticated (`az login`)
- Permissions: **Application Administrator** or **Global Administrator** in your Entra ID tenant
- The DocTalk API deployed and accessible via HTTPS

## Configuration Summary

| Setting                      | Value                                                          |
| ---------------------------- | -------------------------------------------------------------- |
| App type                     | API (server)                                                   |
| Supported account types      | Single tenant (your org only)                                  |
| API scope                    | `api://<APP_ID>/Podcasts.ReadWrite`                            |
| Redirect URI                 | `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect` |
| accessTokenAcceptedVersion   | 2 (v2.0 tokens)                                               |

## Option A: Automated Script

```bash
# From the repo root:
./infra/scripts/register-entra-app.sh
```

The script will:
1. Create the Entra ID app registration
2. Set the Application ID URI (`api://<app-id>`)
3. Add the `Podcasts.ReadWrite` scope
4. Configure the redirect URI for Teams OAuth
5. Set `accessTokenAcceptedVersion` to 2
6. Output `ENTRA_CLIENT_ID` and `ENTRA_TENANT_ID` for use in other config files

After running, export the values printed by the script:
```bash
export ENTRA_CLIENT_ID="<value from script>"
export ENTRA_TENANT_ID="<value from script>"
```

## Option B: Manual Steps (Azure Portal)

### 1. Register the Application

1. Go to [Azure Portal → Entra ID → App registrations](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps)
2. Click **+ New registration**
3. Fill in:
   - **Name**: `DocTalk API`
   - **Supported account types**: *Accounts in this organizational directory only (Single tenant)*
   - **Redirect URI**: Platform = **Web**, URI = `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`
4. Click **Register**

### 2. Note the IDs

From the **Overview** page, record:
- **Application (client) ID** → use as `ENTRA_CLIENT_ID`
- **Directory (tenant) ID** → use as `ENTRA_TENANT_ID`

### 3. Set the Application ID URI

1. Go to **Expose an API**
2. Click **Set** next to "Application ID URI"
3. Accept the default (`api://<client-id>`) or set a custom one
4. Click **Save**

### 4. Add the API Scope

1. Still on **Expose an API**, click **+ Add a scope**
2. Fill in:
   - **Scope name**: `Podcasts.ReadWrite`
   - **Who can consent**: Admins and users
   - **Admin consent display name**: `Read and write podcasts`
   - **Admin consent description**: `Allows the app to generate and manage podcasts on behalf of the user`
   - **User consent display name**: `Read and write your podcasts`
   - **User consent description**: `Allows DocTalk to generate and manage podcasts for you`
   - **State**: Enabled
3. Click **Add scope**

### 5. Set Token Version to v2

1. Go to **Manifest** (JSON editor)
2. Find `"accessTokenAcceptedVersion"` and set it to `2`
3. Click **Save**

## Using the IDs in the Project

Store these as environment variables — **never hardcode them** in source files:

```bash
# .env.dev (gitignored)
ENTRA_CLIENT_ID=<your-client-id>
ENTRA_TENANT_ID=<your-tenant-id>
```

These values are referenced by:
- `appPackage/.env.dev` — Teams Toolkit environment config
- `appPackage/apiSpecificationFile/openapi.yaml` — OAuth security scheme
- `infra/main.bicep` — (if passing to Container Apps as env vars)

## Verification

```bash
# Confirm the app exists
az ad app show --id "$ENTRA_CLIENT_ID" --query "{name:displayName, appId:appId, signInAudience:signInAudience}" -o table

# Confirm the scope exists
az ad app show --id "$ENTRA_CLIENT_ID" --query "api.oauth2PermissionScopes[].{scope:value, enabled:isEnabled}" -o table

# Confirm token version
az ad app show --id "$ENTRA_CLIENT_ID" --query "api.requestedAccessTokenVersion" -o tsv
```

## Cleanup

To delete the registration (e.g., for a fresh start):

```bash
az ad app delete --id "$ENTRA_CLIENT_ID"
```

## Troubleshooting

| Issue                        | Fix                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| 401 on API calls from Copilot | Verify the app scope is consented; check `ENTRA_CLIENT_ID` matches the OpenAPI spec  |
| Token version mismatch       | Ensure `accessTokenAcceptedVersion` is `2` in the manifest                            |
| Redirect URI error           | Must be exactly `https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect`        |
| Scope not visible            | Check Application ID URI is set and scope state is "Enabled"                          |
