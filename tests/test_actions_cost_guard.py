"""Sperrtests des abgeschalteten GitHub-Models-Stundenlaufs (nur statisch)."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "schnapper-hourly.yml"


class LegacyDisabledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_keine_automatischen_stundenlaeufe(self):
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotRegex(self.workflow, r"(?m)^\s*schedule\s*:")
        self.assertNotRegex(self.workflow, r"(?m)^\s*-\s*cron\s*:")

    def test_kein_job_kann_starten_auch_nicht_manuell(self):
        self.assertRegex(self.workflow, r"(?m)^\s+if:\s*\$\{\{\s*false\s*\}\}\s*$")
        self.assertNotIn("team/agent.py", self.workflow)
        self.assertNotIn("curl ", self.workflow)

    def test_keine_modelle_und_keine_schreibrechte(self):
        self.assertRegex(self.workflow, r"(?m)^\s+contents: read\s*$")
        self.assertNotRegex(self.workflow, r"(?m)^\s*models:\s*read")
        self.assertNotRegex(self.workflow, r"(?m)^\s*contents:\s*write")

    def test_oeffentliche_ci_trotzdem_verfuegbar(self):
        tests = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
        self.assertIn("cloudflare-tests:", tests)
        self.assertIn("python-tests:", tests)
        self.assertIn("github.event.repository.private == false", tests)


if __name__ == "__main__":
    unittest.main()
