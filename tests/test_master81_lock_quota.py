"""MASTER 81: sichere Aufruflimits und Lock-Zeitgrenze (reine Offline-Tests)."""
import errno
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import ki
import local_ollama as lokal
from ki import KINichtVerfuegbar


class TestMaster81LokaleGrenzen(unittest.TestCase):
    def setUp(self):
        # Offline unit fixture: consent is tested separately in approval suites.
        consent = mock.patch.object(lokal, "pruefe_freigabe", return_value="S-000")
        consent.start()
        self.addCleanup(consent.stop)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.pfad = pathlib.Path(temp.name) / "work" / "ki_aufrufe.txt"
        patch = mock.patch.dict(os.environ, {
            "SCHNAPPER_KI_BACKEND": "ollama",
            "SCHNAPPER_OLLAMA_MODELL": "qwen2.5:1.5b",
        })
        patch.start()
        self.addCleanup(patch.stop)
        self.ki = lokal.KI(self.pfad)

    def test_sichere_konfigurationswerte_1_bis_6(self):
        self.assertEqual([ki._sicheres_aufruflimit(str(i)) for i in range(1, 7)],
                         list(range(1, 7)))

    def test_ungueltige_konfigurationswerte_sind_gesperrt(self):
        for wert in ("", "0", "7", "8", "600000", "-1", "3.0", " 3",
                     "3 ", "03", "true", "nan", "999999999999999999999"):
            with self.subTest(wert=wert):
                self.assertEqual(ki._sicheres_aufruflimit(wert), 0)

    def test_init_lehnt_null_limit_ohne_modellaufruf_ab(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 0), \
             mock.patch.object(lokal, "_request",
                               side_effect=AssertionError("No Ollama request")):
            with self.assertRaisesRegex(KINichtVerfuegbar, "Aufruflimit"):
                lokal.KI(self.pfad)
        self.assertFalse(self.pfad.exists())

    def test_init_lehnt_limit_ueber_harter_grenze_ab(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 7):
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.pfad)
        self.assertFalse(self.pfad.exists())

    def test_init_lehnt_bool_als_limit_ab(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", True):
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.pfad)

    def test_init_lehnt_float_und_negative_werte_ab(self):
        for limit in (-1, 2.0, "2", None):
            with self.subTest(limit=limit):
                with mock.patch.object(lokal, "MAX_AUFRUFE", limit):
                    with self.assertRaises(KINichtVerfuegbar):
                        lokal.KI(self.pfad)

    def test_limit_eins_wird_respektiert(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 1):
            self.assertEqual(self.ki._zaehle(), 1)
            with self.assertRaisesRegex(KINichtVerfuegbar, "Maximal"):
                self.ki._zaehle()
            self.assertEqual(self.pfad.read_text(), "00000001")

    def test_nachtraeglich_unsicheres_limit_blockiert_ohne_datei(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 999):
            with self.assertRaises(KINichtVerfuegbar):
                self.ki._zaehle()
        self.assertFalse(self.pfad.exists())

    def test_sperre_erfolgreich_ohne_warten(self):
        with mock.patch.object(lokal.fcntl, "flock") as flock:
            lokal._hole_zaehlersperre(123)
        flock.assert_called_once_with(
            123, lokal.fcntl.LOCK_EX | lokal.fcntl.LOCK_NB)

    def test_sperre_retry_bei_eagain(self):
        fehler = BlockingIOError(errno.EAGAIN, "busy")
        with mock.patch.object(lokal.fcntl, "flock", side_effect=[fehler, None]) as lock, \
             mock.patch.object(lokal.time, "monotonic",
                               side_effect=[0.0, 0.5, 0.5]), \
             mock.patch.object(lokal.time, "sleep") as pause:
            lokal._hole_zaehlersperre(123)
        self.assertEqual(lock.call_count, 2)
        pause.assert_called_once()

    def test_sperre_retry_bei_eacces(self):
        fehler = OSError(errno.EACCES, "access conflict")
        with mock.patch.object(lokal.fcntl, "flock", side_effect=[fehler, None]) as lock, \
             mock.patch.object(lokal.time, "monotonic",
                               side_effect=[0.0, 1.0, 1.0]), \
             mock.patch.object(lokal.time, "sleep"):
            lokal._hole_zaehlersperre(123)
        self.assertEqual(lock.call_count, 2)

    def test_sperre_nach_timeout_fehlschlaegt(self):
        fehler = BlockingIOError(errno.EWOULDBLOCK, "busy")
        with mock.patch.object(lokal.fcntl, "flock", side_effect=fehler), \
             mock.patch.object(lokal.time, "monotonic",
                               side_effect=[0.0, 2.01]), \
             mock.patch.object(lokal.time, "sleep") as pause:
            with self.assertRaisesRegex(KINichtVerfuegbar, "Wartezeit"):
                lokal._hole_zaehlersperre(123)
        pause.assert_not_called()

    def test_andere_osfehler_werden_nicht_versteckt(self):
        with mock.patch.object(lokal.fcntl, "flock",
                               side_effect=OSError(errno.EPERM, "denied")):
            with self.assertRaises(OSError):
                lokal._hole_zaehlersperre(123)

    def test_timeout_veraendert_bestehenden_zaehler_nicht(self):
        self.pfad.parent.mkdir()
        self.pfad.write_text("00000003")
        with mock.patch.object(lokal, "_hole_zaehlersperre",
                               side_effect=KINichtVerfuegbar("timeout")):
            with self.assertRaises(KINichtVerfuegbar):
                self.ki._zaehle()
        self.assertEqual(self.pfad.read_text(), "00000003")

    def test_osfehler_bei_sperre_ohne_zaehlermanipulation(self):
        self.pfad.parent.mkdir()
        self.pfad.write_text("00000004")
        with mock.patch.object(lokal, "_hole_zaehlersperre",
                               side_effect=OSError(errno.EPERM, "deny")):
            with self.assertRaisesRegex(KINichtVerfuegbar, "unsicher"):
                self.ki._zaehle()
        self.assertEqual(self.pfad.read_text(), "00000004")

    def test_keine_ausweichende_cloud_api(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 100), \
             mock.patch.object(lokal, "_request") as request:
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.pfad)
        request.assert_not_called()

    def test_sperrenregel_unterliegt_keinem_test_only_skip(self):
        self.assertGreater(lokal.LOCK_WARTEZEIT_SEKUNDEN, 0)
        self.assertLessEqual(lokal.LOCK_WARTEZEIT_SEKUNDEN, 3)
        self.assertEqual(lokal.MAX_SICHERE_AUFRUFE, 6)


if __name__ == "__main__":
    unittest.main()
