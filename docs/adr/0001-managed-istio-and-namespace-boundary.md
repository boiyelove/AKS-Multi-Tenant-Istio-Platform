# ADR 0001: Managed Istio with a namespace tenancy boundary

Status: accepted

## Decision

Use the AKS managed Istio add-on and model a tenant as one Kubernetes namespace
with a dedicated service account, quota, namespaced RBAC, Cilium
NetworkPolicies, and Istio security policy. Platform policy remains
cluster-scoped and is never delegated to tenant owners.

## Consequences

Azure manages mesh lifecycle integration and the bundle remains small and
reviewable. Tenants share nodes and control planes, so the pattern is suitable
only where that trust boundary is accepted. A tenant requiring administrator
rights, custom CNI, custom mesh control plane, or stronger failure isolation
must receive a dedicated cluster.
