"""Strukturprüfung des S-000-Konzepts gegen seine Akzeptanzkriterien."""
import pathlib
import re
import unittest

KONZEPT = pathlib.Path(__file__).resolve().parents[1] / "team" / "konzept" / "S-000-mvp-konzept.md"


def abschnitt(text, titel):
    m = re.search(r"^## " + re.escape(titel) + r".*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


class TestKonzeptS000(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = KONZEPT.read_text(encoding="utf-8")

    def test_lead_genau_drei_mvp_funktionen_mit_begruendung(self):
        lead = abschnitt(self.text, "LEAD")
        punkte = re.findall(r"^\d+\. \*\*", lead, re.M)
        self.assertEqual(len(punkte), 3)
        self.assertEqual(lead.count("Begründung:"), 3)

    def test_brain_ablauf_und_schema(self):
        self.assertIn("Eingabe:", abschnitt(self.text, "BRAIN – Eingabe-Ausgabe-Ablauf"))
        schema = abschnitt(self.text, "BRAIN – minimales Datenfeld-Schema")
        for feld in ("quelle", "quell_id", "preis_cent", "url", "abgerufen_am", "nutzungsrecht_geklaert"):
            self.assertIn(f"`{feld}`", schema)

    def test_keine_integration_behauptet(self):
        self.assertIn("**keine** Anbindung", self.text)

    def test_check_pflichtszenarien_mit_test(self):
        check = abschnitt(self.text, "CHECK")
        for szenario in ("veralteter Preis", "doppeltes Inserat", "fehlende Nutzungsrechte"):
            zeile = next((z for z in check.splitlines() if szenario in z), "")
            self.assertTrue(zeile, szenario)
            self.assertIn("Gegeben", zeile)
            self.assertIn("Dann", zeile)

    def test_command_genau_ein_naechster_schritt(self):
        command = abschnitt(self.text, "COMMAND")
        self.assertIn("**Fertig:**", command)
        self.assertIn("**Nicht fertig:**", command)
        self.assertEqual(command.count("**Nächster Schritt:**"), 1)

    def test_beispieldaten_sind_als_test_erkennbar(self):
        self.assertIn("example.invalid", self.text)
        self.assertNotRegex(self.text, r"https?://(www\.)?(ebay|kleinanzeigen)\.")


if __name__ == "__main__":
    unittest.main()
