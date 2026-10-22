"""S-006: Branches ohne PR, die vollständig in main enthalten sind, als Löschkandidaten belegen.

Die Tests prüfen nur lesend mit git. Fehlen die Remote-Branches (z. B. flacher
Klon ohne diese Refs oder Branch bereits gelöscht), wird übersprungen."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Branch -> fester main-Commit, dessen Baum identisch sein muss (None = vollständig
# Vorfahre von main). Bewusst feste Commits statt origin/main: main wandert weiter,
# der Beleg "Inhalt steckt in main" bleibt trotzdem gültig, solange der Vergleichs-
# Commit ein Vorfahre von origin/main ist.
KANDIDATEN = {
    "fix/schnapper-web-main-20261022": "7a0b83e",
    "feature/schnapper-web-quellen-20261022": "7a0b83e",
    "feature/schnapper-angebotskern-20261021": "5343009",
    "fix/schnapper-hourly-rotation-20261021": None,
    "fix/agent-status-fail-closed-20261022": None,
    "fix/ki-team-github-models-20261021": None,
}

OFFENE_PRS = (2, 6, 7, 8, 12, 13, 14, 15, 16)


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _ref_da(ref):
    return _git("rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode == 0


class TestBranchesS006(unittest.TestCase):
    def test_kandidaten_sind_vollstaendig_in_main(self):
        if not _ref_da("origin/main"):
            self.skipTest("origin/main nicht vorhanden")
        geprueft = 0
        for branch, vergleich in KANDIDATEN.items():
            ref = "origin/" + branch
            if not _ref_da(ref) or (vergleich and not _ref_da(vergleich)):
                continue
            with self.subTest(branch=branch):
                if vergleich is None:
                    r = _git("merge-base", "--is-ancestor", ref, "origin/main")
                    self.assertEqual(r.returncode, 0, f"{branch} hat Commits, die nicht in main sind")
                else:
                    r = _git("merge-base", "--is-ancestor", vergleich, "origin/main")
                    self.assertEqual(r.returncode, 0, f"{vergleich} ist nicht (mehr) in main")
                    r = _git("diff", "--quiet", vergleich, ref)
                    self.assertEqual(r.returncode, 0, f"{branch} unterscheidet sich von {vergleich}")
                geprueft += 1
        if geprueft == 0:
            self.skipTest("keine Kandidaten-Branches lokal vorhanden")

    def test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten(self):
        tasks = json.loads((ROOT / "team" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        s006 = next(t for t in tasks if t["id"] == "S-006")
        self.assertEqual(s006["status"], "proposed")
        for branch in KANDIDATEN:
            self.assertIn(branch, s006["hinweis"])
        self.assertIn("Agenten löschen keine Branches", s006["hinweis"])

    def test_s006_nennt_alle_bekannten_offenen_prs(self):
        # Stand 22.10.2026 10:30 UTC (per GitHub-PR-Liste); neue PRs hier nachtragen.
        tasks = json.loads((ROOT / "team" / "tasks.json").read_text(encoding="utf-8"))["tasks"]
        s006 = next(t for t in tasks if t["id"] == "S-006")
        for nr in OFFENE_PRS:
            with self.subTest(pr=nr):
                self.assertRegex(s006["title"], r"#%d\b" % nr)
        # PR #16 wird mit belegtem Befund geführt, nicht nur namentlich
        self.assertIn("fix/schnapper-price-source-integrity-20261022", s006["hinweis"])
        self.assertIn("0b758dd", s006["hinweis"])


if __name__ == "__main__":
    unittest.main()
