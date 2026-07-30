#!/usr/bin/env python3
"""Render an idempotent, reviewable Kubernetes/Istio tenant bundle."""

from __future__ import annotations

import argparse
import ipaddress
import json
import re
from pathlib import Path
from typing import Any

DNS_LABEL = re.compile(r"^[a-z][a-z0-9-]{1,61}[a-z0-9]$")
UUID = re.compile(r"^[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
HOST = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


class ConfigError(ValueError):
    """An unsafe or incomplete tenant request."""


def _validate(config: dict[str, Any]) -> None:
    required = {
        "tenant_id",
        "owner_group",
        "workload_client_id",
        "cpu_quota",
        "memory_quota",
        "pod_quota",
        "allowed_egress_hosts",
    }
    missing = required - config.keys()
    if missing:
        raise ConfigError(f"missing fields: {', '.join(sorted(missing))}")
    if not DNS_LABEL.fullmatch(str(config["tenant_id"])):
        raise ConfigError("tenant_id must be a 3-63 character DNS label")
    for field in ("owner_group", "workload_client_id"):
        if not UUID.fullmatch(str(config[field])):
            raise ConfigError(f"{field} must be a UUID")
    if not isinstance(config["pod_quota"], int) or not 1 <= config["pod_quota"] <= 200:
        raise ConfigError("pod_quota must be an integer from 1 to 200")
    for field in ("cpu_quota", "memory_quota"):
        if not isinstance(config[field], str) or not config[field].strip():
            raise ConfigError(f"{field} must be a non-empty Kubernetes quantity")
    hosts = config["allowed_egress_hosts"]
    if not isinstance(hosts, list) or len(hosts) > 20:
        raise ConfigError("allowed_egress_hosts must contain at most 20 hosts")
    for host in hosts:
        if not isinstance(host, str) or "*" in host or not HOST.fullmatch(host):
            raise ConfigError(f"unsafe egress host: {host!r}")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            pass
        else:
            raise ConfigError("IP literals are not accepted as egress hosts")


def _object(api: str, kind: str, name: str, namespace: str | None = None) -> dict:
    metadata: dict[str, Any] = {
        "name": name,
        "labels": {
            "app.kubernetes.io/managed-by": "tenant-renderer",
            "platform.azure.example/tenant": name if kind == "Namespace" else namespace,
        },
    }
    if namespace:
        metadata["namespace"] = namespace
    return {"apiVersion": api, "kind": kind, "metadata": metadata}


def render(config: dict[str, Any]) -> dict[str, Any]:
    """Return a Kubernetes List in stable order."""
    _validate(config)
    tenant = config["tenant_id"]
    service_account = "tenant-workload"
    items: list[dict[str, Any]] = []

    namespace = _object("v1", "Namespace", tenant)
    namespace["metadata"]["labels"].update(
        {
            "istio.io/rev": "asm-1-23",
            "pod-security.kubernetes.io/enforce": "restricted",
            "pod-security.kubernetes.io/audit": "restricted",
            "pod-security.kubernetes.io/warn": "restricted",
        }
    )
    items.append(namespace)

    quota = _object("v1", "ResourceQuota", "tenant-quota", tenant)
    quota["spec"] = {
        "hard": {
            "requests.cpu": config["cpu_quota"],
            "limits.cpu": config["cpu_quota"],
            "requests.memory": config["memory_quota"],
            "limits.memory": config["memory_quota"],
            "pods": str(config["pod_quota"]),
            "services.loadbalancers": "0",
        }
    }
    items.append(quota)

    limits = _object("v1", "LimitRange", "tenant-defaults", tenant)
    limits["spec"] = {
        "limits": [
            {
                "type": "Container",
                "defaultRequest": {"cpu": "100m", "memory": "128Mi"},
                "default": {"cpu": "500m", "memory": "512Mi"},
            }
        ]
    }
    items.append(limits)

    account = _object("v1", "ServiceAccount", service_account, tenant)
    account["metadata"]["annotations"] = {
        "azure.workload.identity/client-id": config["workload_client_id"]
    }
    account["metadata"]["labels"]["azure.workload.identity/use"] = "true"
    account["automountServiceAccountToken"] = False
    items.append(account)

    role = _object("rbac.authorization.k8s.io/v1", "Role", "tenant-deployer", tenant)
    role["rules"] = [
        {
            "apiGroups": ["", "apps", "batch"],
            "resources": [
                "configmaps",
                "services",
                "deployments",
                "replicasets",
                "statefulsets",
                "jobs",
                "cronjobs",
            ],
            "verbs": ["get", "list", "watch", "create", "update", "patch", "delete"],
        },
        {
            "apiGroups": [""],
            "resources": ["pods", "pods/log"],
            "verbs": ["get", "list", "watch"],
        },
    ]
    items.append(role)

    binding = _object(
        "rbac.authorization.k8s.io/v1", "RoleBinding", "tenant-deployer", tenant
    )
    binding["subjects"] = [
        {"kind": "Group", "name": config["owner_group"], "apiGroup": "rbac.authorization.k8s.io"}
    ]
    binding["roleRef"] = {
        "kind": "Role",
        "name": "tenant-deployer",
        "apiGroup": "rbac.authorization.k8s.io",
    }
    items.append(binding)

    deny = _object("networking.k8s.io/v1", "NetworkPolicy", "default-deny", tenant)
    deny["spec"] = {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]}
    items.append(deny)

    same_tenant = _object(
        "networking.k8s.io/v1", "NetworkPolicy", "allow-same-tenant", tenant
    )
    same_tenant["spec"] = {
        "podSelector": {},
        "policyTypes": ["Ingress"],
        "ingress": [{"from": [{"podSelector": {}}]}],
    }
    items.append(same_tenant)

    dns = _object("networking.k8s.io/v1", "NetworkPolicy", "allow-dns", tenant)
    dns["spec"] = {
        "podSelector": {},
        "policyTypes": ["Egress"],
        "egress": [
            {
                "to": [
                    {
                        "namespaceSelector": {
                            "matchLabels": {
                                "kubernetes.io/metadata.name": "kube-system"
                            }
                        },
                        "podSelector": {"matchLabels": {"k8s-app": "kube-dns"}},
                    }
                ],
                "ports": [
                    {"protocol": "UDP", "port": 53},
                    {"protocol": "TCP", "port": 53},
                ],
            }
        ],
    }
    items.append(dns)

    mtls = _object("security.istio.io/v1beta1", "PeerAuthentication", "strict", tenant)
    mtls["spec"] = {"mtls": {"mode": "STRICT"}}
    items.append(mtls)

    authz = _object(
        "security.istio.io/v1beta1", "AuthorizationPolicy", "same-tenant-only", tenant
    )
    authz["spec"] = {
        "action": "ALLOW",
        "rules": [
            {
                "from": [
                    {
                        "source": {
                            "principals": [
                                f"cluster.local/ns/{tenant}/sa/{service_account}"
                            ]
                        }
                    }
                ]
            }
        ],
    }
    items.append(authz)

    sidecar = _object("networking.istio.io/v1beta1", "Sidecar", "tenant-egress", tenant)
    sidecar["spec"] = {
        "outboundTrafficPolicy": {"mode": "REGISTRY_ONLY"},
        "egress": [
            {
                "hosts": [
                    "./*",
                    "istio-system/*",
                    *[f"./{host}" for host in sorted(config["allowed_egress_hosts"])],
                ]
            }
        ],
    }
    items.append(sidecar)

    for host in sorted(config["allowed_egress_hosts"]):
        entry = _object(
            "networking.istio.io/v1beta1",
            "ServiceEntry",
            "egress-" + host.replace(".", "-")[:54],
            tenant,
        )
        entry["spec"] = {
            "hosts": [host],
            "location": "MESH_EXTERNAL",
            "resolution": "DNS",
            "ports": [{"number": 443, "name": "https", "protocol": "TLS"}],
        }
        items.append(entry)

    return {"apiVersion": "v1", "kind": "List", "items": items}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        bundle = render(config)
    except (OSError, json.JSONDecodeError, ConfigError) as exc:
        parser.error(str(exc))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
