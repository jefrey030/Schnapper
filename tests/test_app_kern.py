"""Tests für den SCHNAPPER-App-Kern (app/schnapper). Nur Standardbibliothek, kein Netz."""
import datetime as dt
import io
import json
import pathlib
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import Angebot, AngebotFehler, Filter, entferne_dubletten, lies_text, suche, warnungen  # noqa: E402
from schnapper.__main__ import main  # noqa: E402
from schnapper.angebot import geld, normalisiere_url  # noqa: E402
from schnapper.quellen import Register  # noqa: E402

JETZT = dt.datetime(2026, 10, 21, 21, 0, tzinfo=dt.timezone.utc)


def roh(**kw):
    d = {"id": "x1", "titel": "Kopfhörer kabellos", "preis": "50,00", "url": "https://shop.example/a/1",
         "quelle": "shop", "erfasst_am": "2026-10-21T20:00:00Z", "referenzpreis": "100"}
    d.update(kw)
    return d


class Preise(unittest.TestCase):
    def test_deutsches_und_englisches_format(self):
        self.assertEqual(geld("1.299,99 €"), Decimal("1299.99"))
        self.assertEqual(geld("1,299.99 €"), Decimal("1299.99"))
        self.assertEqual(geld("12.345,67"), Decimal("12345.67"))
        self.assertEqual(geld("12,345.67"), Decimal("12345.67"))
        self.assertEqual(geld("12.5"), Decimal("12.50"))
        self.assertEqual(geld(0.1 + 0.2), Decimal("0.30"))

    def test_unlesbar_und_bool(self):
        for wert in ("abc", None, True, "NaN", "inf"):
            with self.assertRaises(AngebotFehler):
                geld(wert)

    def test_rabatt_inkl_versand(self):
        a = Angebot.aus_dict(roh(preis="45", versand="5"))
        self.assertEqual(a.gesamtpreis, Decimal("50.00"))
        self.assertEqual(a.rabatt_prozent, Decimal("50.0"))


class HarteRegeln(unittest.TestCase):
    def test_ungueltige_angebote(self):
        faelle = {
            "preis null": roh(preis="0"), "preis negativ": roh(preis="-1"),
            "http statt https": roh(url="http://shop.example/a"), "keine url": roh(url="https://"),
            "fremdwaehrung": roh(waehrung="USD"), "zustand": roh(zustand="super"),
            "id fehlt": roh(id=""), "zukunft": roh(erfasst_am="2099-01-01T00:00:00Z"),
            "versand negativ": roh(versand="-2"), "referenz null": roh(referenzpreis="0"),
        }
        for name, daten in faelle.items():
            with self.subTest(name), self.assertRaises(AngebotFehler):
                Angebot.aus_dict(daten)


class WeicheRegeln(unittest.TestCase):
    def test_veralteter_preis(self):
        a = Angebot.aus_dict(roh(erfasst_am="2026-10-19T20:00:00Z"))
        self.assertTrue(any(w.startswith("veraltet") for w in warnungen(a, JETZT)))
        frisch = Angebot.aus_dict(roh())
        self.assertFalse(any(w.startswith("veraltet") for w in warnungen(frisch, JETZT)))

    def test_betrugsverdacht_nur_bei_neuware(self):
        neu = Angebot.aus_dict(roh(preis="10", zustand="neu"))
        defekt = Angebot.aus_dict(roh(preis="10", zustand="defekt"))
        self.assertTrue(any(w.startswith("betrugsverdacht") for w in warnungen(neu, JETZT)))
        self.assertFalse(any(w.startswith("betrugsverdacht") for w in warnungen(defekt, JETZT)))

    def test_ohne_referenz_keine_ersparnis_behaupten(self):
        a = Angebot.aus_dict(roh(referenzpreis=""))
        self.assertIsNone(a.rabatt_prozent)
        self.assertIn("kein Referenzpreis: Ersparnis nicht belegbar", warnungen(a, JETZT))


class Dubletten(unittest.TestCase):
    def test_url_ohne_tracking_ist_gleich(self):
        self.assertEqual(normalisiere_url("https://www.Shop.example/a/1/?utm_source=x&farbe=rot#oben"),
                         normalisiere_url("https://shop.example/a/1?farbe=rot"))

    def test_gleiche_url_neuester_bleibt(self):
        alt = Angebot.aus_dict(roh(id="alt", erfasst_am="2026-10-21T10:00:00Z", url="https://shop.example/a/1?ref=x"))
        neu = Angebot.aus_dict(roh(id="neu"))
        behalten, entfernt = entferne_dubletten([alt, neu])
        self.assertEqual([a.id for a in behalten], ["neu"])
        self.assertEqual((entfernt[0][0].id, entfernt[0][1].id), ("alt", "neu"))

    def test_gleicher_titel_gleiche_quelle_andere_url(self):
        a = Angebot.aus_dict(roh(id="a", titel="Kopfhörer kabellos schwarz", url="https://shop.example/a/1"))
        b = Angebot.aus_dict(roh(id="b", titel="Kopfhörer, kabellos – schwarz", url="https://shop.example/a/2"))
        self.assertEqual(len(entferne_dubletten([a, b])[0]), 1)

    def test_andere_quelle_ist_vergleich_keine_dublette(self):
        a = Angebot.aus_dict(roh(id="a", quelle="shop"))
        b = Angebot.aus_dict(roh(id="b", quelle="anderer", url="https://anderer.example/p/1"))
        self.assertEqual(len(entferne_dubletten([a, b])[0]), 2)

    def test_deutlich_anderer_preis_keine_dublette(self):
        a = Angebot.aus_dict(roh(id="a", preis="50"))
        b = Angebot.aus_dict(roh(id="b", preis="60", url="https://shop.example/a/2"))
        self.assertEqual(len(entferne_dubletten([a, b])[0]), 2)


class Suche(unittest.TestCase):
    def setUp(self):
        self.angebote = [
            Angebot.aus_dict(roh(id="teuer", preis="90", url="https://s.example/1")),
            Angebot.aus_dict(roh(id="guenstig", preis="40", url="https://s.example/2", zustand="gebraucht")),
            Angebot.aus_dict(roh(id="ohneref", preis="30", referenzpreis="", url="https://s.example/3")),
            Angebot.aus_dict(roh(id="toaster", titel="Toaster", preis="20", url="https://s.example/4")),
            Angebot.aus_dict(roh(id="fake", preis="5", zustand="neu", url="https://s.example/5")),
        ]

    def ids(self, f=None, sortierung="rabatt"):
        return [t.angebot.id for t in suche(self.angebote, f, sortierung, jetzt=JETZT)]

    def test_rabatt_sortierung_und_verdacht_ausgeblendet(self):
        # toaster 80 %, guenstig 60 %, teuer 10 %, ohne Referenzpreis zuletzt; "fake" (95 % bei Neuware) ausgeblendet
        self.assertEqual(self.ids(), ["toaster", "guenstig", "teuer", "ohneref"])

    def test_textsuche_alle_woerter(self):
        self.assertEqual(self.ids(Filter(text="kabellos KOPFHOERER"), "preis"), ["ohneref", "guenstig", "teuer"])
        self.assertEqual(self.ids(Filter(text="kopfhörer bluetooth")), [])

    def test_filter_preis_rabatt_zustand(self):
        self.assertEqual(self.ids(Filter(max_preis=Decimal("40"))), ["toaster", "guenstig", "ohneref"])
        self.assertEqual(self.ids(Filter(min_rabatt=Decimal("60"))), ["toaster", "guenstig"])  # Grenze inklusive
        self.assertEqual(self.ids(Filter(min_rabatt=Decimal("60.1"))), ["toaster"])
        self.assertEqual(self.ids(Filter(zustaende={"gebraucht"})), ["guenstig"])

    def test_unbekannte_sortierung(self):
        with self.assertRaises(ValueError):
            suche(self.angebote, sortierung="zufall")


class Import(unittest.TestCase):
    def test_json_mit_fehlern_bricht_nicht_ab(self):
        text = json.dumps({"angebote": [roh(id="a"), roh(id="b", preis="x"), roh(id="a")]})
        reg = Register()
        reg.erlaube("shop", "Test-Shop", "erfundene Testquelle")
        e = lies_text(text, "json", reg)
        self.assertEqual([a.id for a in e.angebote], ["a"])
        self.assertEqual(len(e.fehler), 2)

    def test_kaputtes_json(self):
        self.assertEqual(len(lies_text("{kaputt", "json").fehler), 1)

    def test_beispieldatei_ende_zu_ende(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main([str(ROOT / "app" / "beispiele" / "angebote.csv"), "--json"])
        daten = json.loads(out.getvalue())
        self.assertEqual(code, 2)  # Eintrag b6 hat einen negativen Preis
        self.assertEqual(daten["eingelesen"], 5)
        self.assertEqual(daten["dubletten_entfernt"], [{"entfernt": "b1", "behalten": "b2"}])
        ids = [t["id"] for t in daten["treffer"]]
        self.assertNotIn("b4", ids)  # Konsole 92 % unter Neupreis -> Betrugsverdacht
        self.assertIn("b3", ids)  # gleiches Produkt, andere Quelle -> bleibt als Vergleich


if __name__ == "__main__":
    unittest.main()
