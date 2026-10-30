"""Regression gate: legacy hourly workflow must remain fully inert.

No YAML dependency: any added active line requires an explicit review.
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
    "name: SCHNAPPER Legacy Stundenlauf (deaktiviert)",
    "on:",
    "  workflow_dispatch:",
    "permissions:",
    "  contents: read",
    "jobs:",
    "  legacy-disabled:",
    "    if: ${{ false }}",
    "    runs-on: ubuntu-24.04",
    "    steps:",
    '      - run: echo "Legacy-Stundenlauf dauerhaft gesperrt. Keine KI-Ausfuehrung."',
]

class LegacyHourlyDisabledTests(unittest.TestCase):
    def test_exact_inert_workflow_contract(self):
        active = [line.rstrip() for line in WORKFLOW.read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.lstrip().startswith("#")]
        self.assertEqual(active, EXPECTED_ACTIVE_LINES)

if __name__ == "__main__":
    unittest.main()
