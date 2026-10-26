"""Abnahme für MISSION und BLITZ sowie End-to-End-Verknüpfungen mit LUPE/Preis."""
import datetime as dt
import json
import pathlib
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.adapter import finde_in  # noqa: E402
from schnapper.alarm import Wunsch  # noqa: E402
from schnapper.blitz import Blitz, BlitzFehler  # noqa: E402
from schnapper.einlesen import Importergebnis, lies_text  # noqa: E402
from schnapper.mission import Mission, MissionsFehler, Missionsspeicher  # noqa: E402
from schnapper.suche import Filter  # noqa: E402
from schnapper.verlauf import Verlauf  # noqa: E402

JETZT = dt.datetime(2026, 10, 26, 12, 0, tzinfo=dt.timezone.utc)


def roh(id="a1", titel="Kopfhörer kabellos", preis="50", referenz="100",
        url="https://shop.example/offer/1", zeit=None):
    return {"id": id, "titel": titel, "preis": preis, "referenzpreis": referenz,
            "url": url, "quelle": "mock", "erfasst_am": (zeit or JETZT.isoformat()),
            "zustand": "gebraucht"}


def angebote(*zeilen):
    daten = lies_text(json.dumps(list(zeilen)), "json", jetzt=JETZT)
    assert not daten.fehler, daten.fehler
    return daten


class Missionen(unittest.TestCase):
    def test_erstellen_bearbeiten_faellig_pause_und_beenden(self):
        with tempfile.TemporaryDirectory() as tmp:
            speicher = Missionsspeicher.laden(pathlib.Path(tmp, "missionen.json"))
            m = speicher.erstellen(name="Kopfhörer", suche="kabellos", max_preis="60",
                                   intervall_minuten=30, jetzt=JETZT)
            self.assertEqual([x.id for x in speicher.faellige(JETZT)], [m.id])
            gespeichert = speicher.lauf_abschliessen(m.id, JETZT)
            self.assertEqual(gespeichert.letzter_lauf_am, JETZT)
            self.assertEqual(speicher.faellige(JETZT + dt.timedelta(minutes=29)), ())
            self.assertEqual([x.id for x in speicher.faellige(JETZT + dt.timedelta(minutes=30))], [m.id])

            bearbeitet = speicher.bearbeiten(m.id, name="Kabellose Kopfhörer", max_preis="55")
            self.assertEqual(bearbeitet.status, "aktiv")
            self.assertEqual(bearbeitet.letzter_lauf_am, JETZT)
            self.assertEqual(bearbeitet.filter().max_preis, Decimal("55.00"))
            self.assertEqual(speicher.pausieren(m.id).status, "pausiert")
            self.assertEqual(speicher.faellige(JETZT + dt.timedelta(days=1)), ())
            self.assertEqual(speicher.fortsetzen(m.id).status, "aktiv")
            self.assertEqual(speicher.beenden(m.id).status, "beendet")
            with self.assertRaises(MissionsFehler):
                speicher.fortsetzen(m.id)

            wiederhergestellt = Missionsspeicher.laden(pathlib.Path(tmp, "missionen.json"))
            self.assertEqual(wiederhergestellt.alle()[0].status, "beendet")
            self.assertEqual(wiederhergestellt.alle()[0].suche, "kabellos")

    def test_ungueltige_felder_und_zeitzonen_werden_abgewiesen(self):
        faelle = [
            {"name": "", "suche": "x"},
            {"name": "x", "suche": ""},
            {"name": "x", "suche": "x", "intervall_minuten": 14},
            {"name": "x", "suche": "x", "intervall_minuten": True},
            {"name": "x", "suche": "x", "max_preis": "NaN"},
            {"name": "x", "suche": "x", "min_rabatt": "Infinity"},
            {"name": "x", "suche": "x", "zustaende": ["super"]},
            {"name": "x", "suche": "x", "jetzt": "2026-10-26T12:00:00"},
        ]
        for daten in faelle:
            with self.subTest(daten=daten), self.assertRaises(MissionsFehler):
                Mission.erstellen(**daten)

    def test_beschaedigte_missionen_bleiben_unberuehrt(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "missionen.json")
            for text in ('{"version":3,"missionen":[]}', "{kaputt"):
                pfad.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(MissionsFehler):
                    Missionsspeicher.laden(pfad)
                self.assertEqual(pfad.read_text(encoding="utf-8"), text)

    def test_speicherfehler_veraendert_missionsstatus_nicht(self):
        with tempfile.TemporaryDirectory() as tmp:
            speicher = Missionsspeicher.laden(pathlib.Path(tmp, "missionen.json"))
            mission = speicher.erstellen(name="Kopfhörer", suche="kabellos", jetzt=JETZT)
            with mock.patch("schnapper.mission.schreibe_fd", side_effect=OSError("voll")):
                with self.assertRaises(MissionsFehler):
                    speicher.pausieren(mission.id)
            self.assertEqual(speicher.alle()[0].status, "aktiv")


class BlitzQueue(unittest.TestCase):
    def test_neue_passende_angebote_einmalig_und_dauerhaft(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            wunsch = Wunsch.aus_dict({"name": "Kopfhörer", "suche": "kabellos",
                                      "max_preis": "60", "zustaende": ["gebraucht"]})
            liste = angebote(
                roh(id="billig", preis="49", referenz="80"),
                roh(id="zu-teuer", preis="75", url="https://shop.example/offer/2"),
                roh(id="andere", titel="Toaster", preis="20", url="https://shop.example/offer/3"),
            )
            blitz = Blitz.laden(pfad)
            meldungen = blitz.pruefen(liste, [wunsch], jetzt=JETZT)
            self.assertEqual([m.angebot_id for m in meldungen], ["billig"])
            self.assertEqual(meldungen[0].gesamtpreis, Decimal("49.00"))
            self.assertEqual(blitz.pruefen(liste, [wunsch], jetzt=JETZT), [])

            # Dieselbe Produkt-URL mit anderer Tracking-ID bleibt eine Meldung.
            tracking = angebote(roh(id="neue-id", preis="49",
                                    url="https://www.shop.example/offer/1?utm_source=mail"))
            self.assertEqual(blitz.pruefen(tracking, [wunsch], jetzt=JETZT), [])
            erneut = Blitz.laden(pfad)
            self.assertEqual(erneut.pruefen(liste, [wunsch], jetzt=JETZT), [])
            self.assertEqual(len(erneut), 1)

    def test_verdaechtige_und_veraltete_angebote_losen_keinen_blitz_aus(self):
        wunsch = Wunsch.aus_dict({"name": "Kopfhörer", "suche": "kabellos", "max_preis": "60"})
        alt = roh(id="alt", preis="10", zeit=(JETZT - dt.timedelta(hours=30)).isoformat())
        fake = roh(id="fake", preis="5", referenz="100", zeit=JETZT.isoformat())
        fake["zustand"] = "neu"
        meldungen = Blitz().pruefen(angebote(alt, fake), [wunsch], jetzt=JETZT)
        self.assertEqual(meldungen, [])

    def test_beschaedigte_blitzdatei_wird_nicht_ueberschrieben(self):
        with tempfile.TemporaryDirectory() as tmp:
            pfad = pathlib.Path(tmp, "blitz.json")
            for text in ('{"version":9,"gesehen":{}}', "{kaputt"):
                pfad.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(BlitzFehler):
                    Blitz.laden(pfad)
                self.assertEqual(pfad.read_text(encoding="utf-8"), text)

    def test_speicherfehler_gibt_keine_meldung_als_abgeschlossen_aus(self):
        with tempfile.TemporaryDirectory() as tmp:
            wunsch = Wunsch.aus_dict({"name": "Kopfhörer", "suche": "kabellos", "max_preis": "60"})
            blitz = Blitz.laden(pathlib.Path(tmp, "blitz.json"))
            with mock.patch("schnapper.blitz.schreibe_fd", side_effect=OSError("voll")):
                with self.assertRaises(BlitzFehler):
                    blitz.pruefen(angebote(roh()), [wunsch], jetzt=JETZT)
            self.assertEqual(len(blitz), 0)
            self.assertEqual(blitz.pruefen(angebote(roh()), [wunsch], jetzt=JETZT)[0].angebot_id, "a1")


class Zusammenspiel(unittest.TestCase):
    def test_lupe_entfernt_unzulaessiges_und_dubletten_preisdetektiv_vergleicht(self):
        roh_daten = [
            roh(id="alt", preis="80", zeit=(JETZT - dt.timedelta(days=8)).isoformat()),
            roh(id="aktuell", preis="55", zeit=JETZT.isoformat(),
                url="https://www.shop.example/offer/1?utm_campaign=test"),
            roh(id="andere-quelle", preis="60", referenz="100",
                url="https://other.example/offer/1"),
            roh(id="ungueltig", preis="NaN", url="https://shop.example/offer/bad"),
        ]
        daten = lies_text(json.dumps(roh_daten), "json", jetzt=JETZT)
        self.assertEqual(len(daten.fehler), 1)
        ergebnis = finde_in(daten, Filter(text="KOPFHÖRER kabellos"), "preis", jetzt=JETZT)
        self.assertEqual({t.angebot.id for t in ergebnis.treffer}, {"aktuell", "andere-quelle"})
        self.assertEqual(len(ergebnis.dubletten), 1)
        self.assertEqual(len(ergebnis.fehler), 1)

        verlauf = Verlauf()
        verlauf.aufzeichnen(daten.angebote)
        info = verlauf.info(next(t.angebot for t in ergebnis.treffer if t.angebot.id == "aktuell"))
        self.assertIsNotNone(info)
        self.assertGreaterEqual(info.hoechst, info.tiefst)


if __name__ == "__main__":
    unittest.main()
