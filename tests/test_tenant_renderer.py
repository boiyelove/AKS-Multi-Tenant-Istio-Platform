import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tenant_renderer import ConfigError, render  # noqa: E402


class TenantRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (ROOT / "examples/tenants/team-blue.json").read_text(encoding="utf-8")
        )

    def kinds(self, bundle):
        return {item["kind"]: item for item in bundle["items"]}

    def test_renders_all_isolation_controls_deterministically(self):
        first = render(copy.deepcopy(self.config))
        second = render(copy.deepcopy(self.config))
        self.assertEqual(first, second)
        kinds = self.kinds(first)
        for expected in (
            "Namespace",
            "ResourceQuota",
            "LimitRange",
            "Role",
            "RoleBinding",
            "NetworkPolicy",
            "PeerAuthentication",
            "AuthorizationPolicy",
            "Sidecar",
            "ServiceEntry",
        ):
            self.assertIn(expected, kinds)
        self.assertEqual(kinds["PeerAuthentication"]["spec"]["mtls"]["mode"], "STRICT")
        self.assertEqual(
            kinds["Sidecar"]["spec"]["outboundTrafficPolicy"]["mode"], "REGISTRY_ONLY"
        )

    def test_role_cannot_mutate_rbac_or_policy(self):
        role = self.kinds(render(self.config))["Role"]
        api_groups = {group for rule in role["rules"] for group in rule["apiGroups"]}
        resources = {resource for rule in role["rules"] for resource in rule["resources"]}
        self.assertNotIn("rbac.authorization.k8s.io", api_groups)
        self.assertNotIn("networkpolicies", resources)
        self.assertNotIn("secrets", resources)

    def test_service_account_token_is_not_automounted(self):
        account = self.kinds(render(self.config))["ServiceAccount"]
        self.assertFalse(account["automountServiceAccountToken"])
        self.assertEqual(
            account["metadata"]["annotations"]["azure.workload.identity/client-id"],
            self.config["workload_client_id"],
        )

    def test_rejects_wildcard_egress(self):
        config = copy.deepcopy(self.config)
        config["allowed_egress_hosts"] = ["*.example.com"]
        with self.assertRaises(ConfigError):
            render(config)

    def test_rejects_invalid_quota_and_identity(self):
        for field, value in (("pod_quota", 0), ("owner_group", "cluster-admins")):
            with self.subTest(field=field):
                config = copy.deepcopy(self.config)
                config[field] = value
                with self.assertRaises(ConfigError):
                    render(config)


if __name__ == "__main__":
    unittest.main()
