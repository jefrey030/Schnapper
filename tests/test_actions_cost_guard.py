"""Offline regression tests for fail-closed GitHub Actions cost gating.

These tests inspect the workflow without starting a runner or model API call.
They cannot replace an actual GitHub Actions integration run.
"""
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
            raise AssertionError("Missing multiline job-level guard")
        cls.job_guard = match.group(1)

    def test_private_or_missing_visibility_must_fail_closed(self):
        self.assertIn("toJSON(github.event.repository.private) == 'false'", self.job_guard)
        self.assertNotIn("github.event.repository.private == false", self.job_guard)

    def test_repository_flag_cannot_bypass_visibility(self):
        self.assertIn("vars.SCHNAPPER_OEFFENTLICH == 'true'", self.job_guard)
        self.assertIn("vars.SCHNAPPER_PAUSE != 'true'", self.job_guard)
        self.assertNotIn("||", self.job_guard)

    def test_independent_visibility_check_before_agent_calls(self):
        self.assertIn('Kostenschutz – nur öffentliches Repository', self.workflow)
        self.assertIn('if [ "$privat" != "False" ]', self.workflow)
        guard_step = self.workflow.index('Kostenschutz – nur öffentliches Repository')
        first_agent = self.workflow.index('Agent LEAD – plant und verteilt')
        self.assertLess(guard_step, first_agent)


if __name__ == "__main__":
    unittest.main()
