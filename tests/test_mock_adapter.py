"""S-005/T3: echte Offline-Adaptertests ohne Netzwerk, Fremddaten oder Modellaufrufe."""
import datetime as dt
import pathlib
import socket
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.adapter import MockAdapter, QuelleGesperrt, finde
from schnapper.quellen import Quelle, Register

JETZT = dt.datetime(2026, 10, 22, 9, 0, tzinfo=dt.timezone.utc)


class MockAdapterTests(unittest.TestCase):
    def test_t3_zwei_offline_testangebote(self):
        def netz_verboten(*args, **kwargs):
            raise AssertionError("MockAdapter darf niemals ein Netzwerk verwenden")

        with mock.patch("socket.create_connection", side_effect=netz_verboten), \
             mock.patch.object(socket.socket, "connect", netz_verboten):
            ergebnis = MockAdapter(jetzt=JETZT).lade()
        self.assertEqual(ergebnis.fehler, [])
        self.assertEqual(len(ergebnis.angebote), 2)
        self.assertEqual({a.id for a in ergebnis.angebote}, {"TEST-1", "TEST-2"})
        self.assertTrue(all(a.titel.startswith("TEST ") for a in ergebnis.angebote))
        self.assertTrue(all(a.url.startswith("https://example.invalid/") for a in ergebnis.angebote))
        self.assertTrue(all(a.quelle == "mock" for a in ergebnis.angebote))

    def test_t3_voller_suchablauf_mit_veraltet_markierung(self):
        ergebnis = finde(MockAdapter(jetzt=JETZT), jetzt=JETZT)
        self.assertEqual(len(ergebnis.treffer), 2)
        warnungen = {t.angebot.id: t.warnungen for t in ergebnis.treffer}
        self.assertFalse(any("veraltet" in w for w in warnungen["TEST-1"]))
        self.assertTrue(any("veraltet" in w for w in warnungen["TEST-2"]))

    def test_t3_mockquelle_gesperrt_wenn_register_sperrt(self):
        register = Register(quellen=[Quelle("mock", "Test", "ausgeschlossen")])
        with self.assertRaises(QuelleGesperrt):
            MockAdapter(register=register, jetzt=JETZT).lade()

    def test_t3_keine_verdeckten_fremdquellen(self):
        roh = [{"id": "fremd", "titel": "nicht echt", "quelle": "ebay"}]
        with self.assertRaises(QuelleGesperrt):
            MockAdapter(daten=roh, jetzt=JETZT).lade()

    def test_t3_ungueltige_testdaten_werden_gemeldet(self):
        roh = [{"id": "TEST-kaputt", "titel": "TEST", "preis": -1,
                "url": "https://example.invalid/test", "quelle": "mock",
                "erfasst_am": JETZT.isoformat()}]
        ergebnis = MockAdapter(daten=roh, jetzt=JETZT).lade()
        self.assertEqual(ergebnis.angebote, [])
        self.assertEqual(len(ergebnis.fehler), 1)
        self.assertIn("Preis", ergebnis.fehler[0])

    def test_t3_ungueltige_parameter_werden_abgewiesen(self):
        with self.assertRaises(ValueError):
            MockAdapter(daten="keine liste", jetzt=JETZT)
        with self.assertRaises(ValueError):
            MockAdapter(jetzt=dt.datetime(2026, 10, 22, 9, 0))


if __name__ == "__main__":
    unittest.main()
