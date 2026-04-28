param botName string
param microsoftAppId string
param endpoint string

resource bot 'Microsoft.BotService/botServices@2022-09-15' = {
  name: botName
  location: 'global'
  kind: 'azurebot'
  sku: {
    name: 'F0'
  }
  properties: {
    displayName: botName
    endpoint: endpoint
    msaAppId: microsoftAppId
    msaAppType: 'SingleTenant'
    msaAppTenantId: tenant().tenantId
    isStreamingSupported: false
    publicNetworkAccess: 'Enabled'
  }
}

resource teamsChannel 'Microsoft.BotService/botServices/channels@2022-09-15' = {
  parent: bot
  name: 'MsTeamsChannel'
  location: 'global'
  properties: {
    channelName: 'MsTeamsChannel'
  }
}

output botName string = bot.name
