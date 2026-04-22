targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

param openAiModelName string = 'gpt-5.1'
param openAiModelVersion string = '2025-11-13'
param openAiDeploymentCapacity int = 10

var resourceSuffix = take(uniqueString(subscription().id, environmentName, location), 6)
var tags = { 'azd-env-name': environmentName }

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    name: 'podcast-${resourceSuffix}'
    location: location
    tags: tags
  }
}

module keyVault './modules/keyvault.bicep' = {
  name: 'keyvault'
  scope: rg
  params: {
    name: 'kv-podcast-${resourceSuffix}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module openAi './modules/openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    name: 'oai-podcast-${resourceSuffix}'
    location: location
    tags: tags
    modelName: openAiModelName
    modelVersion: openAiModelVersion
    deploymentCapacity: openAiDeploymentCapacity
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module speech './modules/speech.bicep' = {
  name: 'speech'
  scope: rg
  params: {
    name: 'speech-podcast-${resourceSuffix}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module storage './modules/storage.bicep' = {
  name: 'storage'
  scope: rg
  params: {
    name: 'stpodcast${resourceSuffix}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_OPENAI_ENDPOINT string = openAi.outputs.endpoint
output AZURE_OPENAI_DEPLOYMENT_NAME string = openAi.outputs.deploymentName
output AZURE_SPEECH_REGION string = location
output AZURE_SPEECH_RESOURCE_ID string = speech.outputs.resourceId
output AZURE_STORAGE_ACCOUNT_NAME string = storage.outputs.accountName
output AZURE_STORAGE_CONTAINER_NAME string = storage.outputs.containerName
output AZURE_KEY_VAULT_NAME string = keyVault.outputs.name
output AZURE_LOG_ANALYTICS_WORKSPACE_ID string = monitoring.outputs.logAnalyticsWorkspaceId
