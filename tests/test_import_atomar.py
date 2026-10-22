"""Regression: Ein fehlgeschlagener Verlaufsspeicher darf keinen Import aktivieren.

Kein Netzwerk, keine Cloud und keine kostenpflichtigen Dienste.
"""
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import Importergebnis  # noqa: E402
from schnapper.quellen import Register  # noqa: E402
from schnapper.web import Zustand  # noqa: E402


class ImportZustand(unittest.TestCase):
    def setUp(self):
        self.alt = Importergebnis()
        self.neu = Importergebnis()
        self.zustand = Zustand(Register(), self.alt, "vorher.csv", True)

    def test_speicherfehler_aktiviert_neue_liste_nicht(self):
        with mock.patch.object(self.zustand, "preise_merken", side_effect=OSError("Festplatte voll")):
            with self.assertRaises(OSError):
                self.zustand.ersetzen(self.neu, "neu.csv")
        daten, name, beispiel = self.zustand.lesen()
        self.assertIs(daten, self.alt)
        self.assertEqual(name, "vorher.csv")
        self.assertTrue(beispiel)

    def test_liste_wird_erst_nach_gespeichertem_verlauf_aktiviert(self):
        def pruefe_reihenfolge(geladen):
            self.assertIs(geladen, self.neu)
            daten, name, beispiel = self.zustand.lesen()
            self.assertIs(daten, self.alt)
            self.assertEqual(name, "vorher.csv")
            self.assertTrue(beispiel)

        with mock.patch.object(self.zustand, "preise_merken", side_effect=pruefe_reihenfolge) as speichern:
            self.zustand.ersetzen(self.neu, "neu.csv")
            speichern.assert_called_once_with(self.neu)
        daten, name, beispiel = self.zustand.lesen()
        self.assertIs(daten, self.neu)
        self.assertEqual(name, "neu.csv")
        self.assertFalse(beispiel)

    def test_ohne_verlauf_bleibt_import_moeglich(self):
        self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertIs(self.zustand.lesen()[0], self.neu)


if __name__ == "__main__":
    unittest.main()
