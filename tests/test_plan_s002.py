"""Prüft den S-002-Plan: jede Quelle hat Beleg und Entscheidung, kein Scraping-Ziel freigegeben."""
import pathlib
import re
import unittest

DOK = pathlib.Path(__file__).resolve().parents[1] / "team" / "konzept" / "S-002-datenquellen-plan.md"
ENTSCHEIDUNGEN = ("**erlaubt**", "**ausgeschlossen**", "**später möglich**")


class TestPlanS002(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = DOK.read_text(encoding="utf-8")
        cls.quellen = [z for z in cls.text.splitlines() if re.match(r"^\| Q\d+ ", z)]

    def test_jede_quelle_hat_genau_eine_entscheidung(self):
        self.assertGreaterEqual(len(self.quellen), 4)
        for zeile in self.quellen:
            self.assertEqual(sum(e in zeile for e in ENTSCHEIDUNGEN), 1, zeile)

    def test_externe_quellen_haben_offiziellen_beleg(self):
        for zeile in self.quellen:
            if "eBay" in zeile or "Kleinanzeigen" in zeile:
                self.assertRegex(zeile, r"\]\(https://[\w.-]*(ebay\.com|kleinanzeigen\.de)/", zeile)

    def test_kleinanzeigen_ausgeschlossen(self):
        zeile = next(z for z in self.quellen if "Kleinanzeigen" in z)
        self.assertIn("**ausgeschlossen**", zeile)

    def test_ebay_nicht_ohne_freigabe(self):
        zeile = next(z for z in self.quellen if "eBay" in z)
        self.assertNotIn("**erlaubt**", zeile)

    def test_testfaelle_und_naechster_schritt(self):
        self.assertEqual(len(re.findall(r"^\| T\d+ \|", self.text, re.M)), 5)
        self.assertEqual(self.text.count("**Nächster Schritt:**"), 1)


if __name__ == "__main__":
    unittest.main()
