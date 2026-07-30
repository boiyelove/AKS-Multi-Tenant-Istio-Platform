import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class RepositorySecurityTests(unittest.TestCase):
    def test_goal_is_ignored(self):
        self.assertIn("goal.md", (ROOT / ".gitignore").read_text())

    def test_infrastructure_has_private_identity_controls(self):
        text = (ROOT / "infra/platform.bicep").read_text()
        for marker in (
            "disableLocalAccounts: true",
            "enablePrivateCluster: true",
            "publicNetworkAccess: 'Disabled'",
            "enableAzureRBAC: true",
            "workloadIdentity",
            "serviceMeshProfile",
            "enablePurgeProtection: true",
        ):
            self.assertIn(marker, text)

    def test_ci_uses_minimal_permissions_and_scans(self):
        text = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("contents: read", text)
        self.assertIn("trivy-action@0.28.0", text)
        self.assertIn("gitleaks-action@v2", text)


if __name__ == "__main__":
    unittest.main()
