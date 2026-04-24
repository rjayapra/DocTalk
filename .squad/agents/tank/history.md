# Tank — History

## Learnings

### Deployment — Webapp bundled into API container (2025-07)
- **ACR:** `crdoctalkmkffp6` (login server: `crdoctalkmkffp6.azurecr.io`)
- **API Container App:** `ca-doctalk-api-mkffp6`
- **Worker Container App:** `ca-doctalk-worker-mkffp6`
- **API public URL:** `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io`
- **Webapp URL:** `https://ca-doctalk-api-mkffp6.wittyfield-14310482.eastus2.azurecontainerapps.io/app/index.html`
- The webapp (static HTML/CSS/JS in `src/webapp/`) is served by FastAPI's StaticFiles at `/app` — no separate infra needed.
- `Dockerfile.api` copies all of `src/` which includes `src/webapp/`, so no Dockerfile changes needed.
- `azd env` was missing `AZURE_CONTAINER_REGISTRY_NAME` and `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER` — set them manually.
- Build command: `az acr build --registry crdoctalkmkffp6 --image "doctalk-api:podcast-dev" --file Dockerfile.api .`
- Deploy command: `az containerapp update --name ca-doctalk-api-mkffp6 --resource-group rg-podcast-dev --image "crdoctalkmkffp6.azurecr.io/doctalk-api:podcast-dev"`
- The `postprovision` hook in `azure.yaml` handles building both images, but for API-only deploys, the manual `az acr build` + `az containerapp update` approach is faster.

### Deployment — Webapp update with title field + playback fix (2025-07-24)
- **Changes deployed:** 
  - Added name input field to webapp UI (src/webapp/index.html)
  - Fixed title display and event delegation for play buttons (src/webapp/app.js)
  - Added title field to GenerateRequest model (src/api/main.py)
- **Build command:** `az acr build --registry crdoctalkmkffp6 --image "doctalk-api:podcast-dev" --file Dockerfile.api .`
- **Deploy command:** `az containerapp update --name ca-doctalk-api-mkffp6 --resource-group rg-podcast-dev --image "crdoctalkmkffp6.azurecr.io/doctalk-api:podcast-dev"`
- **Verification:** Health endpoint returned `{"status":"healthy","service":"doctalk-api","version":"2.0.0"}` and webapp static files served successfully at `/app/index.html`
- **New revision:** `ca-doctalk-api-mkffp6--0000002` deployed and running
- **Deployment time:** ~2 minutes (build + update)
- **No issues encountered** — clean deployment with zero downtime

### Deployment — SAS token fix for audio URLs (2025-07-24)
- **Changes deployed:**
  - API now generates User Delegation SAS tokens at read time for audio blob URLs (src/api/main.py)
  - `_add_sas_token()` helper uses `get_user_delegation_key()` + `generate_blob_sas()` with read-only permission and 1-hour expiry
- **Build command:** `az acr build --registry crdoctalkmkffp6 --image "doctalk-api:podcast-dev" --file Dockerfile.api .`
- **Deploy command:** `az containerapp update --name ca-doctalk-api-mkffp6 --resource-group rg-podcast-dev --image "crdoctalkmkffp6.azurecr.io/doctalk-api:podcast-dev"`
- **Verification:** Health endpoint returned `{"status":"healthy","service":"doctalk-api","version":"2.0.0"}`
- **No issues encountered** — clean build and deploy
