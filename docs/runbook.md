# Operator runbook

## Onboard

1. Validate AKS/Istio versions and the namespace revision label.
2. Create a managed identity and federated credential whose subject is
   `system:serviceaccount:<tenant>:tenant-workload`.
3. Assign only the resource-scoped Azure role the workload needs.
4. Review tenant JSON, render twice, compare output, and run validation.
5. Server-side dry-run, obtain platform/security approval, then apply.
6. Execute the allowed/denied checks in the test matrix and record sanitized
   results with the deployment commit.

## Incident and rollback

For suspected cross-tenant access, stop new deployments, label the namespace
for incident ownership, capture authorization and flow logs, revoke the Azure
federated credential, and apply a deny-all authorization policy. Restore the
last reviewed bundle only after root cause is resolved. Avoid deleting the
namespace before evidence capture.

## Offboard and teardown

Export only approved evidence, revoke Azure role assignments and federated
credentials, then delete the namespace. Confirm no namespace, role binding,
service entry, managed identity assignment, or dashboard remains. Azure
baseline destruction requires change approval and the exact resource group:

```bash
az group delete --name <exact-resource-group> --yes --no-wait
```

Never run teardown against a shared or production resource group.
