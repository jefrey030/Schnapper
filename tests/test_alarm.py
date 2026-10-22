"""Tests für den Preisalarm (BLITZ)."""
import datetime as dt
import io
import json
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import alarm  # noqa: E402
from schnapper.alarm import Wunsch, WunschFehler, lies_wuensche, pruefe_wuensche  # noqa: E402
from schnapper.einlesen import lies_text  # noqa: E402

JETZT = dt.datetime(2026, 10, 21, 21, 0, tzinfo=dt.timezone.utc)


def angebot(**kw):
    d = {"id": "a", "titel": "Kopfhörer kabellos", "preis": "50", "versand": "0", "url": "https://x.example/1",
         "quelle": "mock", "erfasst_am": "2026-10-21T20:00:00Z", "referenzpreis": "120", "zustand": "gebraucht"}
    d.update(kw)
    return d


def geladen(*angebote):
    return lies_text(json.dumps(list(angebote)), "json")


class WunschEinlesen(unittest.TestCase):
    def test_gueltiger_wunsch(self):
        w = Wunsch.aus_dict({"suche": "Kopfhörer", "max_preis": "59,90", "zustaende": "gebraucht"})
        self.assertEqual(w.name, "Kopfhörer")
        self.assertEqual(w.max_preis, Decimal("59.90"))
        self.assertEqual(w.zustaende, frozenset({"gebraucht"}))

    def test_ohne_grenze_ist_kein_alarm(self):
        with self.assertRaisesRegex(WunschFehler, "Höchstpreis oder Mindestrabatt"):
            Wunsch.aus_dict({"suche": "fahrrad"})

    def test_ungueltige_werte(self):
        for daten, text in (({"max_preis": "10"}, "suche"),
                            ({"suche": "x", "max_preis": "abc"}, "Höchstpreis"),
                            ({"suche": "x", "max_preis": "0"}, "größer als 0"),
                            ({"suche": "x", "min_rabatt": "120"}, "zwischen 0 und 100"),
                            ({"suche": "x", "max_preis": "5", "zustaende": ["kaputt"]}, "Zustand")):
            with self.subTest(daten=daten), self.assertRaisesRegex(WunschFehler, text):
                Wunsch.aus_dict(daten)

    def test_nicht_endlicher_rabatt_wird_als_wunschfehler_gemeldet(self):
        for wert in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(rabatt=wert), self.assertRaisesRegex(WunschFehler, "zwischen 0 und 100"):
                Wunsch.aus_dict({"suche": "fahrrad", "min_rabatt": wert})
        liste = lies_wuensche(json.dumps({"wuensche": [
            {"suche": "fahrrad", "min_rabatt": "NaN"},
            {"suche": "helm", "max_preis": "20"},
        ]}))
        self.assertEqual(len(liste.wuensche), 1)
        self.assertEqual(liste.wuensche[0].suche, "helm")
        self.assertEqual(len(liste.fehler), 1)
        self.assertIn("Wunsch 1", liste.fehler[0])

    def test_ungueltiger_zustandstyp_blockiert_liste_nicht(self):
        for wert in (42, True, {"gebraucht": True}):
            with self.subTest(zustaende=wert), self.assertRaisesRegex(WunschFehler, "Liste oder Text"):
                Wunsch.aus_dict({"suche": "fahrrad", "max_preis": "50", "zustaende": wert})
        liste = lies_wuensche(json.dumps({"wuensche": [
            {"suche": "fahrrad", "max_preis": "50", "zustaende": 42},
            {"suche": "helm", "max_preis": "20", "zustaende": ["gebraucht"]},
        ]}))
        self.assertEqual(len(liste.wuensche), 1)
        self.assertEqual(liste.wuensche[0].suche, "helm")
        self.assertEqual(len(liste.fehler), 1)

    def test_liste_meldet_fehler_und_behaelt_rest(self):
        liste = lies_wuensche(json.dumps({"wuensche": [{"suche": "a", "max_preis": "5"}, {"suche": "b"}]}))
        self.assertEqual(len(liste.wuensche), 1)
        self.assertIn("Wunsch 2", liste.fehler[0])

    def test_kaputtes_json(self):
        liste = lies_wuensche("{nicht json")
        self.assertEqual(liste.wuensche, [])
        self.assertIn("kein gültiges JSON", liste.fehler[0])

    def test_obergrenze_anzahl(self):
        liste = lies_wuensche(json.dumps([{"suche": f"x{i}", "max_preis": "5"} for i in range(150)]))
        self.assertEqual(len(liste.wuensche), alarm.MAX_WUENSCHE)
        self.assertTrue(liste.fehler)


class AlarmPruefen(unittest.TestCase):
    def test_preisgrenze_inkl_versand(self):
        w = Wunsch.aus_dict({"suche": "kopfhoerer", "max_preis": "52"})
        drunter = pruefe_wuensche(geladen(angebot(versand="2")), [w], jetzt=JETZT)[0]
        drueber = pruefe_wuensche(geladen(angebot(versand="2.01")), [w], jetzt=JETZT)[0]
        self.assertEqual(len(drunter.treffer), 1)
        self.assertEqual(drueber.treffer, ())

    def test_guenstigstes_zuerst_und_dubletten_weg(self):
        w = Wunsch.aus_dict({"suche": "kopfhoerer", "max_preis": "100"})
        a = pruefe_wuensche(geladen(angebot(id="1", preis="80", url="https://x.example/80"),
                                    angebot(id="2", preis="40", url="https://x.example/40"),
                                    angebot(id="3", preis="40", url="https://x.example/40?utm_source=x",
                                            erfasst_am="2026-10-21T20:30:00Z")),
                            [w], jetzt=JETZT)[0]
        self.assertEqual([t.angebot.id for t in a.treffer], ["3", "1"])
        self.assertEqual(a.bester.angebot.gesamtpreis, Decimal("40.00"))

    def test_betrugsverdacht_loest_keinen_alarm_aus(self):
        w = Wunsch.aus_dict({"suche": "kopfhoerer", "max_preis": "100"})
        a = pruefe_wuensche(geladen(angebot(preis="10", zustand="neu")), [w], jetzt=JETZT)[0]
        self.assertEqual(a.treffer, ())

    def test_veralteter_preis_nur_auf_wunsch(self):
        w = Wunsch.aus_dict({"suche": "kopfhoerer", "max_preis": "100"})
        alt = geladen(angebot(erfasst_am="2026-10-18T09:00:00Z"))
        self.assertEqual(pruefe_wuensche(alt, [w], jetzt=JETZT)[0].treffer, ())
        self.assertEqual(len(pruefe_wuensche(alt, [w], jetzt=JETZT, mit_veraltet=True)[0].treffer), 1)

    def test_zustand_und_rabatt(self):
        w = Wunsch.aus_dict({"suche": "kopfhoerer", "min_rabatt": "50", "zustaende": ["wie_neu"]})
        a = pruefe_wuensche(geladen(angebot(id="1", zustand="gebraucht", url="https://x.example/a"),
                                    angebot(id="2", zustand="wie_neu", preis="70", url="https://x.example/b"),
                                    angebot(id="3", zustand="wie_neu", preis="55", url="https://x.example/c")),
                            [w], jetzt=JETZT)[0]
        self.assertEqual([t.angebot.id for t in a.treffer], ["3"])


class Kommandozeile(unittest.TestCase):
    def lauf(self, *argv):
        aus, err = io.StringIO(), io.StringIO()
        with redirect_stdout(aus), redirect_stderr(err):
            code = alarm.main(list(argv))
        return code, aus.getvalue(), err.getvalue()

    def test_beispieldateien(self):
        beispiel = ROOT / "app" / "beispiele"
        code, aus, _ = self.lauf(str(beispiel / "angebote.csv"), str(beispiel / "wuensche.json"),
                                 "--mit-veraltet", "--json")
        daten = json.loads(aus)
        self.assertEqual(code, 0)
        self.assertEqual(daten["wuensche"], 3)
        namen = {a["name"]: len(a["treffer"]) for a in daten["alarme"]}
        self.assertEqual(namen["Kopfhörer bis 60 €"], 2)
        # Die "Spielkonsole neu für 39 €" ist Betrugsverdacht und darf keinen Alarm auslösen
        self.assertEqual(namen["Spielkonsole stark reduziert"], 0)

    def test_kein_alarm_exitcode_3(self):
        with tempfile.TemporaryDirectory() as d:
            ang, wun = pathlib.Path(d, "a.json"), pathlib.Path(d, "w.json")
            ang.write_text(json.dumps([angebot()]), encoding="utf-8")
            wun.write_text(json.dumps([{"suche": "fahrrad", "max_preis": "10"}]), encoding="utf-8")
            code, aus, _ = self.lauf(str(ang), str(wun))
        self.assertEqual(code, 3)
        self.assertIn("0 Alarm", aus)

    def test_fehlende_datei(self):
        code, _, err = self.lauf("/gibt/es/nicht.csv", "/gibt/es/nicht.json")
        self.assertEqual(code, 1)
        self.assertIn("nicht lesbar", err)


if __name__ == "__main__":
    unittest.main()
