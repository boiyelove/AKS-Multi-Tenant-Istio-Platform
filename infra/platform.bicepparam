// Deployment values for AKS-Multi-Tenant-Istio-Platform (platform.bicep).
// Values are synthetic and safe by default; review placeholders before what-if or deployment.
using './platform.bicep'

// Selects the Azure region explicitly for this environment.
param location = 'westeurope'

// Defines deterministic naming for this example environment.
param environmentName = 'dev'

// Supplies the suffix input separately from the resource template.
param suffix = 'amtipaks'

// Defines deterministic naming for this example environment.
param clusterName = 'example'

// Supplies the kubernetesVersion input separately from the resource template.
param kubernetesVersion = '1.30.9'

// Supplies a synthetic identity or scope identifier; replace it with the approved value.
param adminGroupObjectId = '00000000-0000-4000-8000-000000000001'

// Supplies the nodeVmSize input separately from the resource template.
param nodeVmSize = 'Standard_D4ds_v5'
