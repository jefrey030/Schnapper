"""P0 regression: exact active workflow lines prevent legacy KI reactivation.

This checks the integration branch's own disabled workflow, not the
different workflow variant on PR #147. No external dependencies.
"""
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = Path(os.environ.get(
    "SCHNAPPER_LEGACY_WORKFLOW_PATH",
    str(ROOT / ".github" / "workflows" / "schnapper-hourly.yml"),
))
EXPECTED_ACTIVE_LINES = [
  "name: SCHNAPPER Legacy-KI (aus Sicherheitsgründen stillgelegt)",
  "on:",
  "  workflow_dispatch:",
  "permissions:",
  "  contents: read",
  "jobs:",
  "  legacy-disabled:",
  "    if: ${{ false }}",
  "    runs-on: ubuntu-latest",
  "    timeout-minutes: 1",
  "    steps:",
  "      - name: Legacy-Dienst gesperrt",
  "        run: echo 'Der Legacy-KI-Lauf ist stillgelegt; es wurde keine KI gestartet.'"
]

class LegacyHourlyDisabledTests(unittest.TestCase):
    def test_exact_inert_workflow_contract(self):
        active = [line.rstrip() for line in WORKFLOW.read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(active, EXPECTED_ACTIVE_LINES)

if __name__ == "__main__":
    unittest.main()
