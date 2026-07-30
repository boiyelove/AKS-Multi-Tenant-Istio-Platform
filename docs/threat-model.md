# Threat model

| Threat | Primary control | Verification | Residual risk |
|---|---|---|---|
| Cross-tenant pod traffic | Default deny, same-namespace grant, Istio authorization | Attempt blue-to-red connection | Cluster admins/CNI compromise |
| Plaintext service traffic | Namespace `STRICT` PeerAuthentication | Send non-mTLS request | Mesh/control-plane compromise |
| Arbitrary internet egress | `REGISTRY_ONLY`, explicit ServiceEntry | Request allowed and denied hosts | DNS/direct-IP bypass needs admission controls |
| Kubernetes privilege escalation | Narrow Role; no secrets/RBAC/policy verbs | `kubectl auth can-i` matrix | Vulnerable workload or cluster admin |
| Azure identity theft | Exact workload identity subject; no token automount by default | Request another tenant's Key Vault secret | Mis-scoped Azure role/federation |
| Noisy neighbor | ResourceQuota, LimitRange, bounded nodes | Exhaust CPU/pods | Node/kernel and storage contention |
| Policy deletion | Tenant role excludes policy resources | Attempt patch/delete | Platform operator error |
| Secret leakage in repository | No credentials; Gitleaks CI | Secret scan | Previously published or external data |

## Trust boundaries

Untrusted: tenant code, tenant images, inbound application callers, submitted
tenant JSON. Privileged: subscription owners, AKS administrators, identity
owners, CI maintainers, node access, and Istio control-plane operators.

## Break glass

The organization must own a time-limited, audited Entra group eligible through
PIM. This repository does not create persistent emergency credentials. During
an isolation incident, suspend the tenant namespace, preserve logs, revoke the
federated credential, and only then grant emergency access.
