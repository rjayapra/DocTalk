# Tank — Infrastructure / DevOps

## Role
Owns all Bicep infrastructure modules, AZD configuration, and deployment pipeline.

## Responsibilities
- Create Bicep modules: ACR, ACA Environment, ACA API, ACA Worker, Identity + RBAC
- Update storage.bicep to add queue + table services
- Update main.bicep to wire all new modules
- Update azure.yaml with services section for api + worker
- Ensure KEDA queue scaling rule on worker container app
- Configure managed identities with correct role assignments

## Context
- **Existing infra:** main.bicep (subscription-scoped), modules for openai, speech, storage, keyvault, monitoring
- **Resource suffix:** mkffp6, region: East US 2
- **Subscription:** 24afdf0b-32ab-4e12-80dc-87bda2ae28ef
- **AZD env:** podcast-dev
- **Required RBAC roles:** AcrPull, Storage Queue/Table/Blob Data Contributor, Cognitive Services User/OpenAI User
- **Key Vault quirk:** Cannot set `enablePurgeProtection: false` — omit property
- **ACA design:** Two apps (api = HTTP, worker = KEDA queue trigger), both in same ACA Environment
