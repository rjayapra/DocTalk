extension microsoftGraphV1

@description('Display name for the Entra ID app registration')
param appDisplayName string = 'DocTalk API'

@description('OAuth2 permission scope name exposed by the API')
param scopeName string = 'Podcasts.ReadWrite'

@description('Unique ID for the OAuth2 permission scope')
param scopeId string = newGuid()

resource app 'Microsoft.Graph/applications@v1.0' = {
  displayName: appDisplayName
  uniqueName: 'doctalk-api-app'
  signInAudience: 'AzureADMyOrg'

  web: {
    redirectUris: [
      'https://teams.microsoft.com/api/platform/v1.0/oAuthRedirect'
    ]
  }

  api: {
    requestedAccessTokenVersion: 2
    oauth2PermissionScopes: [
      {
        id: scopeId
        adminConsentDescription: 'Allows the app to generate and manage podcasts on behalf of the user'
        adminConsentDisplayName: 'Read and write podcasts'
        userConsentDescription: 'Allows DocTalk to generate and manage podcasts for you'
        userConsentDisplayName: 'Read and write your podcasts'
        isEnabled: true
        type: 'User'
        value: scopeName
      }
    ]
  }
}

// Note: The Application ID URI (api://{appId}) cannot be set in the same Bicep
// deployment because appId is auto-generated. The postprovision hook in azure.yaml
// sets it via: az ad app update --id <appId> --identifier-uris api://<appId>

output appId string = app.appId
output objectId string = app.id
