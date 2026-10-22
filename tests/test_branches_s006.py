"""S-006: Branches ohne PR, die vollständig in main enthalten sind, als Löschkandidaten belegen.

Die Tests prüfen nur lesend mit git. Fehlen die Remote-Branches (z. B. flacher
Klon ohne diese Refs oder Branch bereits gelöscht), wird übersprungen."""
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Branch -> Commit, dessen Baum identisch sein muss (None = vollständig Vorfahre von main).
# "origin/main" heißt: Der Inhalt des Branches war irgendwann exakt ein Stand von main
# (Baum-Gleichheit mit einem Commit aus der main-Historie). Ein fester Vergleich mit dem
# jeweils neuesten main schlug fehl, sobald main weiterentwickelt wurde.
KANDIDATEN = {
    "fix/schnapper-web-main-20261022": "origin/main",
    "feature/schnapper-web-quellen-20261022": "origin/main",
    "feature/schnapper-angebotskern-20261021": "5343009",
    "fix/schnapper-hourly-rotation-20261021": None,
}


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _baeume_von_main():
    r = _git("log", "--format=%T", "origin/main")
    return set(r.stdout.split()) if r.returncode == 0 else set()


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
                elif vergleich == "origin/main":
                    baum = _git("rev-parse", ref + "^{tree}").stdout.strip()
                    self.assertIn(baum, _baeume_von_main(),
                                  f"{branch}: Inhalt entspricht keinem Stand der main-Historie")
                else:
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


if __name__ == "__main__":
    unittest.main()
