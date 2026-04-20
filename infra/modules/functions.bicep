param planName string
param indexerFunctionName string
param incidentsFunctionName string
param location string
@secure()
param storageConnectionString string
param appSettings array

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: planName
  location: location
  kind: 'linux'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

var functionRuntimeSettings = [
  {
    name: 'FUNCTIONS_WORKER_RUNTIME'
    value: 'python'
  }
  {
    name: 'FUNCTIONS_EXTENSION_VERSION'
    value: '~4'
  }
  {
    name: 'AzureWebJobsStorage'
    value: storageConnectionString
  }
]

resource indexerFunction 'Microsoft.Web/sites@2023-12-01' = {
  name: indexerFunctionName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: concat(functionRuntimeSettings, [for setting in appSettings: {
        name: setting.name
        value: setting.value
      }])
    }
  }
}

resource incidentsFunction 'Microsoft.Web/sites@2023-12-01' = {
  name: incidentsFunctionName
  location: location
  kind: 'functionapp,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      appSettings: concat(functionRuntimeSettings, [for setting in appSettings: {
        name: setting.name
        value: setting.value
      }])
    }
  }
}

output indexerFunctionName string = indexerFunction.name
output indexerDefaultHostName string = indexerFunction.properties.defaultHostName
output incidentsFunctionName string = incidentsFunction.name
output incidentsDefaultHostName string = incidentsFunction.properties.defaultHostName
