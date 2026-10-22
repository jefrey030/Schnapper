"""Regression: imported mock offers must never look like verified live listings."""
import datetime as dt
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.adapter import MockAdapter, finde
from schnapper.web import als_json


class MockPreisKennzeichnung(unittest.TestCase):
    def test_hochgeladenes_mock_angebot_bleibt_deutlich_testdaten(self):
        jetzt = dt.datetime(2026, 10, 22, 9, 0, tzinfo=dt.timezone.utc)
        ergebnis = finde(MockAdapter(jetzt=jetzt), jetzt=jetzt)
        daten = als_json(ergebnis, name="meine-eigene-liste.csv", beispiel=False)
        self.assertFalse(daten["beispieldaten"])
        self.assertTrue(daten["enthaelt_testdaten"])
        self.assertEqual(len(daten["treffer"]), 2)

    def test_echte_eigene_liste_zeigt_keine_mock_warnung(self):
        from schnapper.einlesen import Importergebnis
        from schnapper.angebot import Angebot
        from schnapper.adapter import finde_in
        jetzt = dt.datetime(2026, 10, 22, 9, 0, tzinfo=dt.timezone.utc)
        angebot = Angebot.aus_dict({
            "id": "own-1", "titel": "Selbst eingetragenes Buch", "preis": "10",
            "url": "https://example.org/own-1", "quelle": "eigene",
            "erfasst_am": jetzt.isoformat()}, jetzt=jetzt)
        daten = als_json(finde_in(Importergebnis(angebote=[angebot]), jetzt=jetzt),
                         name="eigen.csv", beispiel=False)
        self.assertFalse(daten["beispieldaten"])
        self.assertFalse(daten["enthaelt_testdaten"])

    def test_handy_zeigt_banner_auch_bei_hochgeladenen_mock_daten(self):
        quelltext = (ROOT / "app" / "schnapper" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("daten.enthaelt_testdaten", quelltext)
        self.assertIn("daten.beispieldaten || daten.enthaelt_testdaten", quelltext)


if __name__ == "__main__":
    unittest.main()
