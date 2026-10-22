"""Regressionen: Geldwerte nicht falsch verkleinern; kaputte Datensaetze isolieren.

Null Netzwerk, keine Cloud-/Modell-Aufrufe, keine bezahlten Dienste.
"""
import json
import pathlib
import sys
import unittest
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.angebot import Angebot, AngebotFehler, geld, normalisiere_url
from schnapper.alarm import Wunsch, WunschFehler, lies_wuensche
from schnapper.einlesen import lies_text
from schnapper.quellen import Register


def roh(**andere):
    daten = {
        "id": "test", "titel": "TEST Radio", "preis": "19,99",
        "url": "https://shop.example/p/1", "quelle": "mock",
        "erfasst_am": "2026-10-21T12:00:00Z",
    }
    daten.update(andere)
    return daten


class PreisGuardrails(unittest.TestCase):
    def test_gemischte_euroformate_richtig(self):
        faelle = {
            "1.299,99 €": Decimal("1299.99"),
            "1,299.99 EUR": Decimal("1299.99"),
            "12.345,67": Decimal("12345.67"),
            "12,345.67": Decimal("12345.67"),
            "1.234.567,89": Decimal("1234567.89"),
            "1,234,567.89": Decimal("1234567.89"),
            "12,5": Decimal("12.50"),
            "12.5": Decimal("12.50"),
            "1 234": Decimal("1234.00"),
        }
        for wert, erwartet in faelle.items():
            with self.subTest(wert=wert):
                self.assertEqual(geld(wert), erwartet)

    def test_mehrdeutige_und_falsch_gruppierte_betraege_abweisen(self):
        falsch = (
            "1,234", "1.234", "12,34.56", "12.34,56.78",
            "1,23.456", "1,234,56", "1.234.567", "1,234,567",
            "1,2999", "1.2999", "1e4", ".5",
        )
        for wert in falsch:
            with self.subTest(wert=wert), self.assertRaises(AngebotFehler):
                geld(wert)

    def test_kaputter_preis_bricht_restimport_nicht_ab(self):
        e = lies_text(json.dumps([
            roh(id="falsch", preis="1,234"),
            roh(id="okay", preis="12,50", url="https://shop.example/p/2"),
        ]), "json")
        self.assertEqual([a.id for a in e.angebote], ["okay"])
        self.assertEqual(len(e.fehler), 1)

    def test_kaputter_url_import_rest_weiter(self):
        e = lies_text(json.dumps([
            roh(id="falsch", url="https://[kaputt"),
            roh(id="okay", url="https://shop.example/p/2"),
        ]), "json")
        self.assertEqual([a.id for a in e.angebote], ["okay"])
        self.assertEqual(len(e.fehler), 1)
        self.assertIn("URL", e.fehler[0])

    def test_kaputte_urls_werden_als_angebotsfehler_gemeldet(self):
        faelle = (
            "https://[kaputt", "https://shop.example:abc/p",
            "https://shop.example:0/p", "https://nutzer:pass@shop.example/p",
        )
        for url in faelle:
            with self.subTest(url=url), self.assertRaises(AngebotFehler):
                Angebot.aus_dict(roh(url=url))

    def test_url_port_bleibt_differenzierbar(self):
        basis = "https://shop.example/a"
        self.assertEqual(normalisiere_url(basis), normalisiere_url("https://www.shop.example:443/a/?utm_source=x"))
        self.assertNotEqual(normalisiere_url(basis), normalisiere_url("https://shop.example:8443/a"))
        self.assertEqual(normalisiere_url("https://[2001:db8::1]:8443/a"), "https://[2001:db8::1]:8443/a")


class AlarmGuardrails(unittest.TestCase):
    def test_nicht_endliche_rabatte_fuehren_zu_wunschfehler(self):
        for wert in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(wert=wert), self.assertRaisesRegex(WunschFehler, "zwischen 0 und 100"):
                Wunsch.aus_dict({"suche": "Fahrrad", "min_rabatt": wert})

    def test_ungueltige_zustandstypen_abweisen(self):
        for z in (42, {"gebraucht": True}, True):
            with self.subTest(z=z), self.assertRaisesRegex(WunschFehler, "Zustand"):
                Wunsch.aus_dict({"suche": "Fahrrad", "max_preis": "100", "zustaende": z})

    def test_defekte_wuensche_ueberspringen_statt_alle_verwerfen(self):
        liste = lies_wuensche(json.dumps({"wuensche": [
            {"suche": "Fahrrad", "min_rabatt": "NaN"},
            {"suche": "Kopfhörer", "max_preis": "50", "zustaende": ["gebraucht"]},
        ]}))
        self.assertEqual(len(liste.fehler), 1)
        self.assertEqual([w.suche for w in liste.wuensche], ["Kopfhörer"])


if __name__ == "__main__":
    unittest.main()
