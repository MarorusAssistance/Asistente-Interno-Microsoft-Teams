param baseName string
param location string
param enableApplicationInsights bool

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = if (enableApplicationInsights) {
  name: take('${baseName}-law', 63)
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = if (enableApplicationInsights) {
  name: take('${baseName}-appi', 260)
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    IngestionMode: 'LogAnalytics'
  }
}

output connectionString string = enableApplicationInsights ? insights.properties.ConnectionString : ''
output appInsightsName string = enableApplicationInsights ? insights.name : ''
