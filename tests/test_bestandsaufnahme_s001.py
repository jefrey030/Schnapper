"""Prüft, dass die S-001-Bestandsaufnahme nur Belegbares nennt."""
import ast
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOK = ROOT / "team" / "konzept" / "S-001-bestandsaufnahme.md"


class TestBestandsaufnahmeS001(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOK.read_text(encoding="utf-8")

    def test_genannte_funktionen_existieren(self):
        paare = re.findall(r"^- `([\w/.]+\.py): (\w+)`", self.text, re.M)
        self.assertGreaterEqual(len(paare), 10)
        for datei, name in paare:
            baum = ast.parse((ROOT / datei).read_text(encoding="utf-8"))
            namen = {n.name for n in baum.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
            self.assertIn(name, namen, f"{datei}: {name}")

    def test_genannte_dateien_existieren(self):
        for pfad in re.findall(r"^- `([\w/.-]+\.(?:md|yml))`", self.text, re.M):
            self.assertTrue((ROOT / pfad).is_file(), pfad)

    def test_nur_standardbibliothek(self):
        self.assertFalse((ROOT / "requirements.txt").exists())
        erlaubt = {"json", "pathlib", "re", "subprocess", "sys", "datetime", "os", "urllib", "ki", "runner"}
        for datei in (ROOT / "team").glob("*.py"):
            baum = ast.parse(datei.read_text(encoding="utf-8"))
            for n in ast.walk(baum):
                mods = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                       [n.module] if isinstance(n, ast.ImportFrom) and n.module else []
                for m in mods:
                    self.assertIn(m.split(".")[0], erlaubt, f"{datei.name}: {m}")

    def test_fehlende_schnittstellen_und_blocker(self):
        self.assertEqual(len(re.findall(r"^\| M\d+ \|", self.text, re.M)), 8)
        self.assertIn("Nutzungsrechte", self.text)
        self.assertIn("Kontosperre/Billing", self.text)


if __name__ == "__main__":
    unittest.main()
