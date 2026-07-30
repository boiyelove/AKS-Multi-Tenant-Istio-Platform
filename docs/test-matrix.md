# Test matrix

| Scenario | Expected result | Automated locally |
|---|---|---|
| Render valid request twice | Byte-identical bundles | Yes |
| Wildcard egress or invalid group | Request rejected | Yes |
| Tenant Role mutates RBAC/secrets/policy | No verbs granted | Yes |
| Blue calls blue using mTLS | Allowed and observable | Live cluster |
| Blue calls red | Denied by network/authz policy | Live cluster |
| Plaintext request | Denied by strict mTLS | Live cluster |
| Allowed HTTPS host | Allowed through mesh | Live cluster |
| Unlisted host/direct IP | Denied and logged | Live cluster |
| Blue identity reads red Key Vault | Azure 403 | Live Azure |
| Pod quota exhausted | Additional pod rejected | Live cluster |
| CPU noisy neighbor | Quota enforced; platform alert | Live cluster/load |
| Tenant patches isolation policy | RBAC forbidden | Live cluster |
| Reapply/offboard/re-onboard | Idempotent; no orphan grants | Live cluster |
| Resource-group teardown | No billable resources remain | Disposable Azure |

Live evidence must identify Azure region, resource versions, Git commit,
timestamp, tester, and sanitized correlation IDs. Never commit subscription
IDs, tenant IDs, access tokens, kubeconfigs, or customer telemetry.
