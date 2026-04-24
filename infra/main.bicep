targetScope = 'subscription'

@minLength(1)
@maxLength(64)
param environmentName string

@minLength(1)
param location string

param openAiModelName string = 'gpt-5.1'
param openAiModelVersion string = '2025-11-13'
param openAiDeploymentCapacity int = 10
param queueName string = 'podcast-jobs'
param tableName string = 'podcastjobs'

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
    queueName: queueName
    tableName: tableName
  }
}

module registry './modules/registry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    name: 'crdoctalk${resourceSuffix}'
    location: location
    tags: tags
  }
}

module containerAppEnv './modules/container-app-env.bicep' = {
  name: 'containerAppEnv'
  scope: rg
  params: {
    name: 'cae-doctalk-${resourceSuffix}'
    location: location
    tags: tags
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
  }
}

module identity './modules/identity.bicep' = {
  name: 'identity'
  scope: rg
  params: {
    name: 'id-doctalk-${resourceSuffix}'
    location: location
    tags: tags
    storageAccountId: storage.outputs.id
    acrId: registry.outputs.id
  }
}

module apiApp './modules/container-app-api.bicep' = {
  name: 'apiApp'
  scope: rg
  params: {
    name: 'ca-doctalk-api-${resourceSuffix}'
    location: location
    tags: tags
    environmentId: containerAppEnv.outputs.id
    registryLoginServer: registry.outputs.loginServer
    identityId: identity.outputs.apiIdentityId
    identityClientId: identity.outputs.apiIdentityClientId
    openAiEndpoint: openAi.outputs.endpoint
    speechRegion: location
    speechResourceId: speech.outputs.resourceId
    storageAccountName: storage.outputs.accountName
    queueName: queueName
    tableName: tableName
    containerName: storage.outputs.containerName
    appInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
  }
}

module workerApp './modules/container-app-worker.bicep' = {
  name: 'workerApp'
  scope: rg
  params: {
    name: 'ca-doctalk-worker-${resourceSuffix}'
    location: location
    tags: tags
    environmentId: containerAppEnv.outputs.id
    registryLoginServer: registry.outputs.loginServer
    identityId: identity.outputs.workerIdentityId
    identityClientId: identity.outputs.workerIdentityClientId
    openAiEndpoint: openAi.outputs.endpoint
    speechRegion: location
    speechResourceId: speech.outputs.resourceId
    storageAccountName: storage.outputs.accountName
    queueName: queueName
    tableName: tableName
    containerName: storage.outputs.containerName
    appInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
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
output AZURE_CONTAINER_REGISTRY_LOGIN_SERVER string = registry.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.name
output AZURE_CONTAINER_APP_ENV_NAME string = containerAppEnv.outputs.name
output DOCTALK_API_URL string = 'https://${apiApp.outputs.fqdn}'
output AZURE_STORAGE_QUEUE_NAME string = queueName
output AZURE_STORAGE_TABLE_NAME string = tableName
