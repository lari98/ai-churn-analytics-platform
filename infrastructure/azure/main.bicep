// ─────────────────────────────────────────────────────────────────────────────
// Azure Infrastructure — AI Churn Analytics Platform
// Bicep IaC template (Azure Well-Architected Framework)
// Deploy: az deployment group create --resource-group rg-churn-analytics
//         --template-file main.bicep --parameters @parameters.json
// ─────────────────────────────────────────────────────────────────────────────

@description('Environment: dev | staging | prod')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'prod'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Project name prefix for all resource names')
param projectName string = 'churnanalytics'

@description('Administrator object ID for Key Vault access policies')
param adminObjectId string

@secure()
@description('Azure SQL admin password')
param sqlAdminPassword string

var prefix = '${projectName}-${environment}'
var tags = {
  Project: 'AIChurnAnalytics'
  Environment: environment
  ManagedBy: 'Bicep'
  GDPRCompliant: 'true'
  CostCenter: 'AI-Platform'
}

// ── Key Vault ─────────────────────────────────────────────────────────────────
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'kv-${prefix}'
  location: location
  tags: tags
  properties: {
    sku: { family: 'A', name: 'premium' }
    tenantId: subscription().tenantId
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
    enableRbacAuthorization: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
  }
}

// ── Storage Account (ADLS Gen2) ───────────────────────────────────────────────
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'adls${projectName}${environment}'
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: { name: 'Standard_GRS' }
  properties: {
    isHnsEnabled: true            // ADLS Gen2
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false  // No public access
    encryption: {
      services: {
        blob: { enabled: true, keyType: 'Account' }
        file: { enabled: true, keyType: 'Account' }
      }
      keySource: 'Microsoft.Storage'
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
    }
  }
}

// ── Azure SQL Database ────────────────────────────────────────────────────────
resource sqlServer 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: 'sql-${prefix}'
  location: location
  tags: tags
  properties: {
    administratorLogin: 'churn_admin'
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Disabled'   // Private endpoint only
  }
}

resource sqlDatabase 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  parent: sqlServer
  name: 'churn-analytics'
  location: location
  tags: tags
  sku: { name: 'BusinessCritical', tier: 'BusinessCritical', capacity: 4 }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 107374182400  // 100 GB
    zoneRedundant: true
    backupStorageRedundancy: 'GeoZone'
  }
}

resource sqlTDE 'Microsoft.Sql/servers/databases/transparentDataEncryption@2022-05-01-preview' = {
  parent: sqlDatabase
  name: 'current'
  properties: { state: 'Enabled' }
}

// ── Azure Container Apps Environment ─────────────────────────────────────────
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-${prefix}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 90
  }
}

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${prefix}'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-churn-api-${environment}'
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: ['https://app.churn-analytics.azure.com']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE']
          allowCredentials: true
        }
      }
      secrets: [
        { name: 'db-connection-string', keyVaultUrl: '${keyVault.properties.vaultUri}secrets/db-connection-string', identity: 'system' }
        { name: 'openai-api-key',        keyVaultUrl: '${keyVault.properties.vaultUri}secrets/openai-api-key',        identity: 'system' }
        { name: 'pii-masking-salt',      keyVaultUrl: '${keyVault.properties.vaultUri}secrets/pii-masking-salt',      identity: 'system' }
      ]
    }
    template: {
      containers: [{
        name: 'churn-api'
        image: 'acrchurnanalytics.azurecr.io/churn-api:latest'
        resources: { cpu: json('1.0'), memory: '2Gi' }
        env: [
          { name: 'ENVIRONMENT',     value: environment }
          { name: 'DATABASE_URL',    secretRef: 'db-connection-string' }
          { name: 'AZURE_OPENAI_API_KEY', secretRef: 'openai-api-key' }
          { name: 'PII_MASKING_SALT', secretRef: 'pii-masking-salt' }
        ]
      }]
      scale: { minReplicas: 2, maxReplicas: 10 }
    }
  }
}

// ── Azure Cache for Redis ─────────────────────────────────────────────────────
resource redisCache 'Microsoft.Cache/redis@2023-04-01' = {
  name: 'redis-${prefix}'
  location: location
  tags: tags
  properties: {
    sku: { name: 'Standard', family: 'C', capacity: 1 }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
    redisConfiguration: { 'maxmemory-policy': 'allkeys-lru' }
  }
}

// ── Outputs ───────────────────────────────────────────────────────────────────
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output keyVaultUri string = keyVault.properties.vaultUri
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output storageAccountName string = storageAccount.name
