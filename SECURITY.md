# Security Policy

## Supported versions

Security fixes are applied to the latest release on `main`.

## Reporting

Use GitHub private vulnerability reporting. Do not open a public issue for an
unpatched isolation bypass. Include the affected version, tenant configuration,
reproduction steps, and impact without real credentials or customer data.

## Deployment assumptions

Treat cluster administrators, subscription owners, node access, Istio control
plane access, and the tenant identity provisioning process as privileged.
Require pull-request review for `infra/`, `src/`, and generated-policy tests.
Use workload identity rather than secrets, private API connectivity, Defender,
image admission controls, and an organization-owned emergency process.

The sample does not create federated identity credentials, Azure role
assignments, Pod Security Admission policy exemptions, or a break-glass
principal. Those controls must be governed outside the tenant bundle.
