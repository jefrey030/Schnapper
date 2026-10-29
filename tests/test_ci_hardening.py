"""Offline-Prüfung der CI-Sicherheitsgrenzen, ohne GitHub-API oder externe Kosten."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"


class CiHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_node24_kompatible_actions(self):
        self.assertEqual(self.workflow.count("actions/checkout@v7"), 2)
        self.assertIn("actions/setup-python@v7", self.workflow)
        self.assertIn("actions/setup-node@v7", self.workflow)
        self.assertNotIn("actions/checkout@v4", self.workflow)
        self.assertNotIn("actions/setup-python@v5", self.workflow)
        self.assertNotIn("actions/setup-node@v4", self.workflow)

    def test_runner_stabil_und_budgetgeschuetzt(self):
        self.assertEqual(self.workflow.count("runs-on: ubuntu-24.04"), 2)
        self.assertEqual(self.workflow.count("github.event.repository.private == false"), 2)
        self.assertEqual(self.workflow.count("timeout-minutes: 5"), 2)
        self.assertNotIn("runs-on: ubuntu-latest", self.workflow)

    def test_read_only_und_ohne_deployment(self):
        self.assertIn("contents: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertNotIn("models: read", self.workflow)
        self.assertEqual(self.workflow.count("persist-credentials: false"), 2)
        self.assertIn("package-manager-cache: false", self.workflow)
        self.assertNotIn("wrangler deploy", self.workflow)
        self.assertNotIn("npm publish", self.workflow)

    def test_regressionen_bleiben_aktiv(self):
        self.assertIn("python -m unittest discover -s tests -v", self.workflow)
        self.assertIn("node --test test/*.test.mjs", self.workflow)
        self.assertIn("working-directory: cloudflare", self.workflow)


if __name__ == "__main__":
    unittest.main()
