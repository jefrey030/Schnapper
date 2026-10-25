"""MASTER 90: Offline regression of the disabled Actions AI job."""
from pathlib import Path
import re
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "schnapper-hourly.yml"

class HourlyWorkflowCostGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(r"(?m)^    if: >-\n((?:      [^\n]*\n)+)", cls.workflow)
        if match is None:
            raise AssertionError("Job-level guard fehlt")
        cls.job_guard = match.group(1)

    def test_alter_stundenplan_und_api_rechte_entfernt(self):
        self.assertNotIn("schedule:", self.workflow)
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("models: read", self.workflow)
        self.assertNotIn("contents: write", self.workflow)
        self.assertIn("contents: read", self.workflow)

    def test_job_ist_immer_gesperrt_auch_bei_gesetztem_flag(self):
        self.assertTrue(self.job_guard.lstrip().startswith("false &&"))
        self.assertIn("toJSON(github.event.repository.private) == 'false'", self.job_guard)
        self.assertNotIn("github.event.repository.private == false", self.job_guard)
        self.assertIn("vars.SCHNAPPER_OEFFENTLICH == 'true'", self.job_guard)
        self.assertIn("vars.SCHNAPPER_PAUSE != 'true'", self.job_guard)
        self.assertNotIn("||", self.job_guard)

    def test_keine_latenten_agenten_und_git_schreibschritte(self):
        for verboten in ("GITHUB_TOKEN", "team/agent.py", "git push",
                         "git pull", "team/ki.py", "SCHNAPPER_MODELL",
                         "secrets.GITHUB_TOKEN"):
            self.assertNotIn(verboten, self.workflow)

if __name__ == "__main__":
    unittest.main()
