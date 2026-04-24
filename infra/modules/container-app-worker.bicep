param name string
param location string = resourceGroup().location
param tags object = {}
param environmentId string
param registryLoginServer string
param identityId string
param identityClientId string
param openAiEndpoint string
param speechRegion string
param speechResourceId string
param storageAccountName string
param queueName string
param tableName string
param containerName string
param appInsightsConnectionString string
param imageTag string = 'latest'

// Get storage account key for KEDA queue scaling
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource workerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'worker' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: registryLoginServer
          identity: identityId
        }
      ]
      secrets: [
        {
          name: 'storage-connection'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};AccountKey=${storageAccount.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: '${registryLoginServer}/doctalk-worker:${imageTag}'
          resources: {
            cpu: json('1')
            memory: '2Gi'
          }
          env: [
            { name: 'AZURE_CLIENT_ID', value: identityClientId }
            { name: 'AZURE_OPENAI_ENDPOINT', value: openAiEndpoint }
            { name: 'AZURE_OPENAI_DEPLOYMENT_NAME', value: 'gpt-51' }
            { name: 'AZURE_SPEECH_REGION', value: speechRegion }
            { name: 'AZURE_SPEECH_RESOURCE_ID', value: speechResourceId }
            { name: 'AZURE_STORAGE_ACCOUNT_NAME', value: storageAccountName }
            { name: 'AZURE_STORAGE_CONTAINER_NAME', value: containerName }
            { name: 'AZURE_STORAGE_QUEUE_NAME', value: queueName }
            { name: 'AZURE_STORAGE_TABLE_NAME', value: tableName }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 5
        rules: [
          {
            name: 'queue-scaling'
            azureQueue: {
              queueName: queueName
              queueLength: 1
              auth: [
                {
                  secretRef: 'storage-connection'
                  triggerParameter: 'connection'
                }
              ]
            }
          }
        ]
      }
    }
  }
}

output name string = workerApp.name
