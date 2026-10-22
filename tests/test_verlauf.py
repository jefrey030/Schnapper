"""Tests für den Preisverlauf."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.angebot import Angebot  # noqa: E402
from schnapper.verlauf import MAX_PUNKTE, Verlauf, VerlaufFehler, warnung  # noqa: E402

START = dt.datetime(2025, 1, 1, 12, 0, tzinfo=dt.timezone.utc)


def angebot(preis, tag=0, url="https://x.example/a/1", referenz=None, versand="0"):
    return Angebot.aus_dict({
        "id": f"a{tag}", "titel": "Kopfhörer", "preis": preis, "versand": versand, "url": url, "quelle": "mock",
        "erfasst_am": (START + dt.timedelta(days=tag)).isoformat(), "referenzpreis": referenz})


class Aufzeichnen(unittest.TestCase):
    def test_gleiche_beobachtung_nur_einmal(self):
        v = Verlauf()
        self.assertEqual(v.aufzeichnen([angebot("50")]), 1)
        self.assertEqual(v.aufzeichnen([angebot("50")]), 0)  # dieselbe Liste noch einmal geladen
        self.assertEqual(len(v), 1)

    def test_tracking_parameter_egal(self):
        v = Verlauf()
        v.aufzeichnen([angebot("60", 0, url="https://www.x.example/a/1/?utm_source=mail")])
        info = v.info(angebot("50", 3))
        self.assertIsNotNone(info)
        self.assertEqual(info.vorher, Decimal("60.00"))

    def test_obergrenze_punkte(self):
        v = Verlauf()
        v.aufzeichnen([angebot(str(10 + i), i) for i in range(MAX_PUNKTE + 20)])
        punkte = v._daten["https://x.example/a/1"]
        self.assertEqual(len(punkte), MAX_PUNKTE)
        self.assertEqual(punkte[0][1], Decimal("30.00"))  # die ältesten 20 sind weg


class Auswerten(unittest.TestCase):
    def test_ohne_vorgeschichte_keine_info(self):
        self.assertIsNone(Verlauf().info(angebot("50")))

    def test_tiefstpreis_und_aenderung(self):
        v = Verlauf()
        v.aufzeichnen([angebot("80", 0), angebot("70", 5)])
        info = v.info(angebot("55", 10))
        self.assertTrue(info.ist_tiefstpreis)
        self.assertEqual((info.tiefst, info.hoechst), (Decimal("55.00"), Decimal("80.00")))
        self.assertEqual(info.vorher, Decimal("70.00"))
        self.assertEqual(info.seit_tagen, 10)

    def test_versand_zaehlt_mit(self):
        v = Verlauf()
        v.aufzeichnen([angebot("50", 0, versand="0")])
        info = v.info(angebot("45", 2, versand="10"))
        self.assertFalse(info.ist_tiefstpreis)  # 55 € inkl. Versand ist teurer
        self.assertEqual(info.vorher, Decimal("50.00"))

    def test_gleicher_preis_ist_keine_aenderung(self):
        v = Verlauf()
        v.aufzeichnen([angebot("60", 0), angebot("50", 1)])
        info = v.info(angebot("50", 2))
        self.assertIsNone(info.vorher)

    def test_alte_beobachtungen_ausserhalb_fenster(self):
        v = Verlauf()
        v.aufzeichnen([angebot("20", 0), angebot("90", 35)])
        info = v.info(angebot("80", 40))
        self.assertEqual(info.tiefst, Decimal("80.00"))  # die 20 € von vor 40 Tagen zählen nicht

    def test_geschoenter_referenzpreis(self):
        v = Verlauf()
        v.aufzeichnen([angebot("59", 0), angebot("62", 4), angebot("60", 8)])
        info = v.info(angebot("55", 10, referenz="149"))
        self.assertTrue(info.referenz_fragwuerdig)
        self.assertIn("nie über 62,00 €", warnung(info))

    def test_referenzpreis_nicht_zu_frueh_verdaechtigen(self):
        v = Verlauf()
        v.aufzeichnen([angebot("59", 0), angebot("62", 2)])  # nur 3 Tage beobachtet
        info = v.info(angebot("55", 3, referenz="149"))
        self.assertFalse(info.referenz_fragwuerdig)
        self.assertIsNone(warnung(info))

    def test_plausibler_referenzpreis(self):
        v = Verlauf()
        v.aufzeichnen([angebot("99", 0), angebot("89", 5), angebot("79", 9)])
        self.assertFalse(v.info(angebot("59", 10, referenz="99")).referenz_fragwuerdig)


class Datei(unittest.TestCase):
    def test_speichern_und_laden(self):
        with tempfile.TemporaryDirectory() as d:
            pfad = pathlib.Path(d, "unterordner", "verlauf.json")
            v = Verlauf(pfad)
            v.aufzeichnen([angebot("80", 0), angebot("70", 5)])
            v.speichern()
            neu = Verlauf.laden(pfad)
            self.assertEqual(neu.info(angebot("60", 6)).hoechst, Decimal("80.00"))
            self.assertEqual(list(pathlib.Path(d, "unterordner").iterdir()), [pfad])  # keine Hilfsdatei übrig

    def test_fehlende_datei_ist_leer(self):
        self.assertEqual(len(Verlauf.laden("/gibt/es/nicht.json")), 0)

    def test_beschaedigte_datei_wird_nicht_ueberschrieben(self):
        with tempfile.TemporaryDirectory() as d:
            pfad = pathlib.Path(d, "verlauf.json")
            for inhalt in ("{kaputt", json.dumps({"version": 99, "angebote": {}}),
                           json.dumps({"version": 1, "angebote": {"u": [["2026-10-01T00:00:00", "-5"]]}})):
                pfad.write_text(inhalt, encoding="utf-8")
                with self.subTest(inhalt=inhalt), self.assertRaises(VerlaufFehler):
                    Verlauf.laden(pfad)
                self.assertEqual(pfad.read_text(encoding="utf-8"), inhalt)


if __name__ == "__main__":
    unittest.main()
