"""S-006: PR-Übersicht team/konzept/S-006-pr-uebersicht.md belegen.

Struktur wird immer geprüft. Zahlen werden nur nachgerechnet, wenn die PR-Köpfe
lokal vorhanden sind (z. B. nach `git fetch origin pull/N/head`), sonst Überspringen.
Vergleich gegen festen main-Commit, damit wanderndes main den Beleg nicht bricht."""
import pathlib
import re
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
DOK = ROOT / "team" / "konzept" / "S-006-pr-uebersicht.md"
BASIS = "4bc37e7"

from test_branches_s006 import OFFENE_PRS  # noqa: E402  (gleiche PR-Liste wie S-006)

ZEILE = re.compile(
    r"^\| #(\d+) \| ([0-9a-f]{7}) \| (\d+) \| (\d+) \| (ok|Konflikt) \| ([^|]*) \|$", re.M)


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)


def _da(ref):
    return _git("rev-parse", "--verify", "--quiet", ref + "^{commit}").returncode == 0


def _zeilen():
    return {int(m[0]): m[1:] for m in ZEILE.findall(DOK.read_text(encoding="utf-8"))}


class TestPrUebersichtS006(unittest.TestCase):
    def test_alle_offenen_prs_genau_einmal(self):
        text = DOK.read_text(encoding="utf-8")
        zeilen = ZEILE.findall(text)
        self.assertEqual(sorted(int(z[0]) for z in zeilen), sorted(OFFENE_PRS))
        self.assertIn("Agenten mergen und schließen keine PRs", text)
        self.assertIn(BASIS, text)

    def test_zahlen_stimmen_mit_git(self):
        if not _da(BASIS):
            self.skipTest("Basis-Commit nicht vorhanden")
        geprueft = 0
        zeilen = _zeilen()
        for nr, (kopf, commits, dateien, merge, enthalten) in zeilen.items():
            if not _da(kopf):
                continue
            with self.subTest(pr=nr):
                n = _git("rev-list", "--count", f"{BASIS}..{kopf}").stdout.strip()
                self.assertEqual(n, commits)
                f = _git("diff", "--name-only", f"{BASIS}...{kopf}").stdout.split()
                self.assertEqual(len(f), int(dateien))
                r = _git("merge-tree", "--write-tree", BASIS, kopf)
                if r.returncode in (0, 1):  # andere Codes: git zu alt für --write-tree
                    self.assertEqual("ok" if r.returncode == 0 else "Konflikt", merge)
                for ziel in re.findall(r"#(\d+)", enthalten):
                    ziel_kopf = zeilen[int(ziel)][0]
                    if _da(ziel_kopf):
                        r = _git("merge-base", "--is-ancestor", kopf, ziel_kopf)
                        self.assertEqual(r.returncode, 0, f"#{nr} nicht in #{ziel}")
                geprueft += 1
        if geprueft == 0:
            self.skipTest("keine PR-Köpfe lokal vorhanden")


if __name__ == "__main__":
    unittest.main()
