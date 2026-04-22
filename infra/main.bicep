param projectName string
param environmentName string
param location string
param postgresAdminUser string
@secure()
param postgresAdminPassword string
param postgresDatabaseName string
@secure()
param openAiApiKey string
param chatModel string
param embeddingModel string
param embeddingDimensions int
@secure()
param adminApiKey string
@secure()
param appSharedSecret string
param microsoftAppId string
@secure()
param microsoftAppPassword string
param allowedOrigins array = []
param enableApplicationInsights bool = true

var projectSlug = toLower(replace(projectName, '_', '-'))
var envSlug = toLower(replace(environmentName, '_', '-'))
var baseName = '${projectSlug}-${envSlug}'
var webAppPlanName = take('${baseName}-plan', 40)
var webAppName = take('${baseName}-web', 60)
var functionsPlanName = take('${baseName}-func-plan', 40)
var indexerFunctionName = take('${baseName}-indexer', 60)
var incidentsFunctionName = take('${baseName}-incidents', 60)
var storageAccountName = toLower(take('st${uniqueString(resourceGroup().id, projectName, environmentName)}', 24))
var postgresServerName = take('${baseName}-pg', 63)
var postgresHost = '${postgresServerName}.postgres.database.azure.com'
var databaseUrl = 'postgresql+psycopg://${postgresAdminUser}:${uriComponent(postgresAdminPassword)}@${postgresHost}:5432/${postgresDatabaseName}?sslmode=require'

module storage './modules/storage.bicep' = {
  name: '${baseName}-storage'
  params: {
    storageAccountName: storageAccountName
    location: location
  }
}

module appInsights './modules/app-insights.bicep' = {
  name: '${baseName}-insights'
  params: {
    baseName: baseName
    location: location
    enableApplicationInsights: enableApplicationInsights
  }
}

var storageConnectionString = storage.outputs.connectionString

module postgres './modules/postgres.bicep' = {
  name: '${baseName}-postgres'
  params: {
    serverName: postgresServerName
    location: location
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    databaseName: postgresDatabaseName
  }
}

var commonAppSettings = [
  {
    name: 'APP_ENV'
    value: environmentName
  }
  {
    name: 'APP_NAME'
    value: 'internal-assistant-mvp'
  }
  {
    name: 'DATABASE_URL'
    value: databaseUrl
  }
  {
    name: 'LLM_PROVIDER'
    value: 'openai'
  }
  {
    name: 'EMBEDDINGS_PROVIDER'
    value: 'openai'
  }
  {
    name: 'OPENAI_API_KEY'
    value: openAiApiKey
  }
  {
    name: 'CHAT_MODEL'
    value: chatModel
  }
  {
    name: 'EMBEDDING_MODEL'
    value: embeddingModel
  }
  {
    name: 'EMBEDDING_DIMENSIONS'
    value: string(embeddingDimensions)
  }
  {
    name: 'ADMIN_API_KEY'
    value: adminApiKey
  }
  {
    name: 'APP_SHARED_SECRET'
    value: appSharedSecret
  }
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: appInsights.outputs.connectionString
  }
  {
    name: 'LOG_LEVEL'
    value: 'INFO'
  }
]

var webAppHostname = '${webAppName}.azurewebsites.net'
var indexerFunctionHostname = '${indexerFunctionName}.azurewebsites.net'
var incidentsFunctionHostname = '${incidentsFunctionName}.azurewebsites.net'
var botEndpoint = 'https://${webAppHostname}/api/messages'

module appService './modules/app-service.bicep' = {
  name: '${baseName}-app-service'
  params: {
    planName: webAppPlanName
    webAppName: webAppName
    location: location
    allowedOrigins: join(allowedOrigins, ',')
    appSettings: concat(commonAppSettings, [
      {
        name: 'ALLOWED_ORIGINS'
        value: join(allowedOrigins, ',')
      }
      {
        name: 'BOT_ENDPOINT'
        value: botEndpoint
      }
      {
        name: 'CUSTOM_INCIDENTS_API_BASE_URL'
        value: 'https://${incidentsFunctionHostname}/api'
      }
      {
        name: 'INDEXER_API_BASE_URL'
        value: 'https://${indexerFunctionHostname}/api'
      }
      {
        name: 'MICROSOFT_APP_ID'
        value: microsoftAppId
      }
      {
        name: 'MICROSOFT_APP_PASSWORD'
        value: microsoftAppPassword
      }
      {
        name: 'PYTHONPATH'
        value: '/home/site/wwwroot:/home/site/wwwroot/src:/home/site/wwwroot/.python_packages/lib/site-packages'
      }
      {
        name: 'WEBSITE_RUN_FROM_PACKAGE'
        value: '0'
      }
      {
        name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
        value: 'true'
      }
    ])
  }
}

module functions './modules/functions.bicep' = {
  name: '${baseName}-functions'
  params: {
    planName: functionsPlanName
    indexerFunctionName: indexerFunctionName
    incidentsFunctionName: incidentsFunctionName
    location: location
    storageConnectionString: storageConnectionString
    appSettings: concat(commonAppSettings, [
      {
        name: 'CUSTOM_INCIDENTS_API_BASE_URL'
        value: 'https://${incidentsFunctionHostname}/api'
      }
      {
        name: 'INDEXER_API_BASE_URL'
        value: 'https://${indexerFunctionHostname}/api'
      }
      {
        name: 'PYTHONPATH'
        value: '/home/site/wwwroot:/home/site/wwwroot/src:/home/site/wwwroot/.python_packages/lib/site-packages'
      }
      {
        name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
        value: 'true'
      }
      {
        name: 'ENABLE_ORYX_BUILD'
        value: 'true'
      }
      {
        name: 'AzureWebJobsFeatureFlags'
        value: 'EnableWorkerIndexing'
      }
    ])
  }
}

module bot './modules/bot.bicep' = {
  name: '${baseName}-bot'
  params: {
    botName: take('${baseName}-bot', 42)
    microsoftAppId: microsoftAppId
    endpoint: botEndpoint
  }
}

output webAppName string = appService.outputs.webAppName
output webAppHostname string = appService.outputs.defaultHostName
output indexerFunctionName string = functions.outputs.indexerFunctionName
output indexerFunctionHostname string = functions.outputs.indexerDefaultHostName
output incidentsFunctionName string = functions.outputs.incidentsFunctionName
output incidentsFunctionHostname string = functions.outputs.incidentsDefaultHostName
output postgresServerName string = postgres.outputs.serverName
output storageAccountName string = storage.outputs.storageAccountName
output botName string = bot.outputs.botName
output applicationInsightsConnectionString string = appInsights.outputs.connectionString
