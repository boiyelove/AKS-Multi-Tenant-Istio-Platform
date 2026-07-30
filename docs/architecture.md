# Architecture

## Context and components

Platform operators deploy the Azure baseline and own cluster-scoped policy.
Identity owners create a user-assigned managed identity and federated
credential for each approved service account. Tenant owners submit a JSON
request; the renderer produces a reviewable Kubernetes `List`.

The bundle is intentionally namespaced. It cannot establish Azure trust or
cluster-scoped admission policy. That separation keeps tenant onboarding from
quietly escalating identity or control-plane permissions.

## Data and control flow

1. A reviewed Bicep deployment creates private AKS with Azure RBAC, OIDC,
   workload identity, managed Istio, Defender, Key Vault, and monitoring.
2. An identity owner binds the exact issuer, namespace, and service account to
   a managed identity and grants it a resource-scoped Azure role.
3. CI renders a tenant request, tests invariants, and exposes the bundle for
   review.
4. A platform operator applies the bundle. Kubernetes RBAC limits deployment
   actions; Cilium and Istio enforce network and identity boundaries.
5. Azure Monitor and Grafana expose platform signals. Dashboard authorization
   and per-tenant recording rules are organization-specific follow-up work.

## Availability, recovery, and SLOs

The target platform SLO is 99.9% successful authenticated in-cluster requests,
excluding Azure regional outages and tenant-caused quota rejection. Alert on
Istio 5xx above 1% for five minutes, rejected policy changes, node pressure,
and exhausted tenant quotas. Renderer operations are local, atomic, and
idempotent. Re-apply the last reviewed bundle for recovery; Git is the source
of truth. Roll back infrastructure by deploying the previous Bicep revision,
not by editing live resources.

## Cost envelope

Default retention is 30 days and autoscaling is bounded at six system nodes.
Managed Grafana, AKS, logs, Defender, and network egress are chargeable. Budget
alerts and log caps are subscription-level requirements, not created here.

## Limitations

- Namespace isolation is not equivalent to separate clusters or subscriptions.
- Shared kernel, nodes, CNI, DNS, admission, and mesh control plane remain
  correlated-failure and privileged-access domains.
- The fixed Istio revision label must be updated to the revision installed in
  the chosen AKS region before applying a tenant bundle.
- NetworkPolicy cannot authorize DNS names; Istio provides the host allowlist,
  while platform policy must constrain direct-IP and host-network bypasses.
- Grafana private endpoint/DNS, tenant-specific dashboards, federated identity
  resources, image signature enforcement, and Azure role assignments are
  deliberately organization-owned.
- Live integration evidence requires an Azure subscription and is not bundled.
