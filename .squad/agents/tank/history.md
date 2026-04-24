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
