# AKS Multi-Tenant Istio Platform

A production-oriented reference implementation for hard team isolation on a
shared Azure Kubernetes Service cluster. It combines a private AKS baseline
with managed Istio and deterministic tenant bundles containing namespace,
quota, RBAC, workload identity, default-deny networking, strict mTLS,
authorization, and egress controls.

This project demonstrates technical safeguards; it does not make a compliance
or absolute-isolation claim. Kubernetes cluster administrators, Azure
subscription owners, shared nodes, DNS, and the Istio control plane remain
trust boundaries. Use dedicated clusters when those boundaries are not
acceptable.

## Architecture

```mermaid
flowchart LR
  O[Platform operator] -->|Bicep| A[Private AKS]
  A --> I[Managed Istio]
  R[tenant_renderer.py] --> B[Tenant bundle]
  B --> N[Namespace + quota]
  B --> Z[RBAC + workload identity]
  B --> P[NetworkPolicy + mTLS + authz]
  B --> E[Sidecar egress allowlist]
  N --> A
  Z --> A
  P --> I
  E --> I
  A --> M[Azure Monitor workspace]
  A --> G[Managed Grafana]
  Z --> K[Key Vault]
```

See [architecture](docs/architecture.md), [threat model](docs/threat-model.md),
[ADR 0001](docs/adr/0001-managed-istio-and-namespace-boundary.md), and the
[operator runbook](docs/runbook.md).

## Local quickstart

Prerequisites: Python 3.11+, Azure CLI with Bicep, and optionally `kubectl`.

```bash
python3 src/tenant_renderer.py \
  --config examples/tenants/team-blue.json \
  --output build/team-blue.json
python3 -m unittest discover -s tests -v
./scripts/validate.sh
```

Inspect the bundle before applying it:

```bash
kubectl apply --dry-run=server -f build/team-blue.json
kubectl apply -f build/team-blue.json
```

The renderer refuses unsafe tenant IDs, empty owner groups, broad egress
wildcards, and non-positive quotas. Re-running it with the same input produces
the same output.

## Azure deployment

No command runs automatically and Azure deployment is chargeable.

```bash
az deployment sub what-if \
  --location westeurope \
  --template-file infra/main.bicep \
  --parameters environmentName=demo location=westeurope

az deployment sub create \
  --location westeurope \
  --template-file infra/main.bicep \
  --parameters environmentName=demo location=westeurope
```

The deployment creates a resource group, private AKS cluster, Key Vault,
Azure Monitor workspace, and Managed Grafana. Private DNS connectivity from
the operator network and suitable Azure role assignments are deployment
prerequisites. Tenant workload identity federated credentials are deliberately
left to an identity owner because client IDs and issuer trust are
organization-specific.

## Security invariants

- AKS local accounts and public API access are disabled.
- Azure RBAC, OIDC issuer, workload identity, Defender, and managed Istio are
  enabled.
- Every tenant starts with ingress and egress denied.
- DNS, same-namespace traffic, and explicit egress hosts are separate grants.
- Istio mutual TLS is `STRICT`; authorization only accepts the tenant service
  account namespace.
- Namespaced operators cannot create RBAC bindings or mutate platform policy.
- Quotas and default limits reduce noisy-neighbor impact but cannot eliminate
  shared-node contention.

## Verification and evidence

`./scripts/validate.sh` compiles Bicep when Azure CLI is available, renders the
sample twice and compares bytes, runs unit/security tests, validates JSON, and
checks shell scripts. CI repeats these gates and runs Trivy configuration and
secret scans. Live AKS denial, recovery, identity, load, and teardown tests are
documented in [the test matrix](docs/test-matrix.md) and require an isolated
Azure subscription.

## Cost and teardown

The dominant costs are AKS nodes, Managed Grafana, and log ingestion. A small
non-production cluster is expected to cost hundreds of USD per month depending
on region, node type, retention, and traffic; use Azure Pricing Calculator
before deployment. Remove tenant resources with
`kubectl delete namespace <tenant>` and the Azure baseline with
`az group delete --name <deployment-output-resource-group>`. See the runbook
for safeguards and evidence collection.

## Project status

This is a `v0.1.0` reference vertical slice. Known limitations are documented
in [the architecture](docs/architecture.md#limitations). See
[SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md),
[SUPPORT.md](SUPPORT.md), and [CHANGELOG.md](CHANGELOG.md).
