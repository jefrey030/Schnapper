"""MASTER 84: Integration der S-006-Branch-Pruefung, ohne Git-Schreiboperation.

Ausschliesslich Offline-Tests: kein Netzwerk, keine Branch-Loeschung,
kein Merge, keine KI-Inferenz und keine Produktionsaktion.
"""
import os
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import test_branches_s006 as s006


class TestMaster84S006Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = (ROOT / ".github" / "workflows" / "tests.yml").read_text(
            encoding="utf-8")

    def test_fuenf_remote_referenzziele_explizit_im_ci(self):
        wanted = ("main", *s006.KANDIDATEN)
        for branch in wanted:
            with self.subTest(branch=branch):
                self.assertIn(
                    "+refs/heads/" + branch + ":refs/remotes/origin/" + branch,
                    self.workflow)

    def test_ci_uses_full_history_instead_of_shallow_clone(self):
        self.assertIn("fetch-depth: 0", self.workflow)

    def test_credentials_not_persisted_and_read_only(self):
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn("permissions:\n  contents: read", self.workflow)

    def test_no_deploy_or_branch_delete_in_s006_ci_step(self):
        start = self.workflow.index(
            "- name: S-006 alle Remote-Refs fuer Integrationspruefung laden")
        end = self.workflow.index("- uses: actions/setup-python", start)
        step = self.workflow[start:end]
        self.assertIn("git fetch --no-tags --no-recurse-submodules", step)
        for prohibited in ("git push", "git branch -D", "git merge",
                           "gh pr merge", "git reset --hard",
                           "curl ", "wget ", "deploy"):
            with self.subTest(term=prohibited):
                self.assertNotIn(prohibited, step)

    def test_ci_os_versions_remain_pinned_to_ubuntu_2404(self):
        self.assertEqual(self.workflow.count("runs-on: ubuntu-24.04"), 2)

    def test_ci_actions_remain_current_in_both_jobs(self):
        self.assertIn("actions/checkout@v7", self.workflow)
        self.assertIn("actions/setup-python@v7", self.workflow)
        self.assertIn("actions/setup-node@v7", self.workflow)

    def test_ci_still_disables_private_repo_runners(self):
        self.assertEqual(
            self.workflow.count("if: github.event.repository.private == false"),
            2)

    def test_ci_requires_all_four_ref_checks(self):
        self.assertIn("self.assertEqual(geprueft, len(KANDIDATEN)", 
                      pathlib.Path(s006.__file__).read_text(encoding="utf-8"))

    def test_ci_fails_when_any_historical_candidate_missing(self):
        missing = "origin/feature/schnapper-angebotskern-20261021"
        def ref_exists(name):
            return name != missing
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
             mock.patch.object(s006, "_ref_da", side_effect=ref_exists):
            with self.assertRaisesRegex(AssertionError, "Git-Referenzen fehlen"):
                s006.TestBranchesS006(
                    "test_kandidaten_sind_vollstaendig_in_main"
                ).test_kandidaten_sind_vollstaendig_in_main()

    def test_local_missing_refs_may_skip_but_ci_never_skips(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}), \
             mock.patch.object(s006, "_ref_da", return_value=False):
            with self.assertRaises(unittest.SkipTest):
                s006.TestBranchesS006(
                    "test_kandidaten_sind_vollstaendig_in_main"
                ).test_kandidaten_sind_vollstaendig_in_main()

    def test_four_mock_candidates_are_really_validated_when_present(self):
        git_calls = []
        def fake_git(*args):
            git_calls.append(args)
            if args[:2] == ("rev-parse", "origin/fix/schnapper-web-main-20261022^{tree}"):
                return SimpleNamespace(returncode=0, stdout="tree123\n")
            if args and args[0] == "rev-parse":
                return SimpleNamespace(returncode=0, stdout="tree123\n")
            return SimpleNamespace(returncode=0, stdout="")
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}), \
             mock.patch.object(s006, "_ref_da", return_value=True), \
             mock.patch.object(s006, "_baeume_von_main",
                               return_value={"tree123"}), \
             mock.patch.object(s006, "_git", side_effect=fake_git):
            s006.TestBranchesS006(
                "test_kandidaten_sind_vollstaendig_in_main"
            ).test_kandidaten_sind_vollstaendig_in_main()
        self.assertEqual(len(git_calls), len(s006.KANDIDATEN))


if __name__ == "__main__":
    unittest.main()
