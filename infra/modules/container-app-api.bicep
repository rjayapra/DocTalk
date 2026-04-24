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
param entraAppId string = ''
param entraTenantId string = ''

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: union(tags, { 'azd-service-name': 'api' })
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
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      registries: [
        {
          server: registryLoginServer
          identity: identityId
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'api'
          image: '${registryLoginServer}/doctalk-api:${imageTag}'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
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
            { name: 'ENTRA_APP_ID', value: entraAppId }
            { name: 'ENTRA_TENANT_ID', value: entraTenantId }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 2
      }
    }
  }
}

output fqdn string = apiApp.properties.configuration.ingress.fqdn
output name string = apiApp.name
