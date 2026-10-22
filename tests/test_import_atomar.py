"""Regression: Ein fehlgeschlagener Verlaufsspeicher darf keinen Import aktivieren.

Kein Netzwerk, keine Cloud und keine kostenpflichtigen Dienste.
"""
import pathlib
import sys
import threading
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

    def test_erneuter_import_speichert_nach_frueherem_fehler_auch_ohne_neue_punkte(self):
        verlauf = mock.Mock()
        verlauf.importiere.side_effect = [OSError("Festplatte voll"), 0]
        self.zustand.verlauf = verlauf

        with self.assertRaises(OSError):
            self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertIs(self.zustand.lesen()[0], self.alt)

        # Ein neuer Import nach dem Schreibfehler muss die Persistenz
        # nochmals ausführen; im echten Verlauf werden Fehler rückgängig gemacht.
        self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertEqual(verlauf.importiere.call_count, 2)
        self.assertIs(self.zustand.lesen()[0], self.neu)

    def test_ohne_verlauf_bleibt_import_moeglich(self):
        self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertIs(self.zustand.lesen()[0], self.neu)


    def test_parallele_importe_werden_serialisiert(self):
        """Langsames Speichern darf einen späteren Import nicht überholen."""
        zweiter = Importergebnis()
        im_ersten_speichern = threading.Event()
        erster_darf_weiter = threading.Event()
        zweiter_gestartet = threading.Event()
        zweiter_speichert = threading.Event()
        fehler = []

        def speichern(geladen):
            if geladen is self.neu:
                im_ersten_speichern.set()
                if not erster_darf_weiter.wait(timeout=3):
                    raise TimeoutError("Erster Import blieb blockiert")
            if geladen is zweiter:
                zweiter_speichert.set()

        def lauf(geladen, name):
            try:
                self.zustand.ersetzen(geladen, name)
            except Exception as exc:
                fehler.append(exc)

        def spaeter():
            zweiter_gestartet.set()
            lauf(zweiter, "zweiter.csv")

        with mock.patch.object(self.zustand, "preise_merken", side_effect=speichern):
            a = threading.Thread(target=lauf, args=(self.neu, "erster.csv"))
            b = threading.Thread(target=spaeter)
            a.start()
            try:
                self.assertTrue(im_ersten_speichern.wait(2), "Erster Import wurde nicht gestartet")
                b.start()
                self.assertTrue(zweiter_gestartet.wait(2))
                b.join(timeout=0.1)
                self.assertFalse(zweiter_speichert.is_set(), "Zweiter Import hat ersten überholt")
                self.assertEqual(self.zustand.lesen()[1], "vorher.csv")
            finally:
                erster_darf_weiter.set()
                a.join(timeout=3)
                if b.ident is not None:
                    b.join(timeout=3)
        self.assertFalse(a.is_alive())
        self.assertFalse(b.is_alive())
        self.assertFalse(fehler, str(fehler))
        self.assertTrue(zweiter_speichert.is_set())
        self.assertEqual(self.zustand.lesen()[1], "zweiter.csv")


if __name__ == "__main__":
    unittest.main()
