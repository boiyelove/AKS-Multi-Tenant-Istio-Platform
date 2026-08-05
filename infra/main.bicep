// AKS-Multi-Tenant-Istio-Platform infrastructure template.
// Resource behavior stays in this file; deployment-time values are supplied by ./main.bicepparam.

targetScope = 'subscription'

// Deployment inputs: values are explicit, reviewable, and environment-specific.

@minLength(2)
@maxLength(12)
@description('Short lowercase environment name used in globally unique resource names.')
param environmentName string

@description('Azure region verified for AKS managed Istio, Managed Grafana, and Azure Monitor workspace.')
param location string

@description('AKS version is intentionally explicit; update after reviewing the compatibility matrix.')
param kubernetesVersion string

@description('Object ID of the Entra group that administers the cluster.')
param adminGroupObjectId string

@allowed([
  'Standard_D4ds_v5'
  'Standard_D4s_v5'
])
param nodeVmSize string

// Derived configuration: constructs deterministic names, IDs, and policy values.
var suffix = uniqueString(subscription().id, environmentName, location)
var resourceGroupName = 'rg-aks-mt-${environmentName}'
var clusterName = 'aks-mt-${environmentName}-${suffix}'

// Resource rg: declares Microsoft.Resources/resourceGroups@2024-03-01 and its security settings.
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: {
    workload: 'aks-multi-tenant-istio'
    environment: environmentName
    managedBy: 'bicep'
  }
}

// Module platform: composes platform.bicep with validated inputs.
module platform 'platform.bicep' = {
  name: 'multiTenantPlatform'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    suffix: suffix
    clusterName: clusterName
    kubernetesVersion: kubernetesVersion
    adminGroupObjectId: adminGroupObjectId
    nodeVmSize: nodeVmSize
  }
}

// Deployment outputs: expose identifiers needed by operators and downstream automation.
output resourceGroupName string = rg.name
output clusterName string = platform.outputs.clusterName
output oidcIssuerUrl string = platform.outputs.oidcIssuerUrl
output keyVaultName string = platform.outputs.keyVaultName
