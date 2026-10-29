"""MASTER 80: Offline-Regressionen fuer den lokalen Ollama-Aufrufzaehler.

Keine Verbindung zu Ollama, keine echten KI-Aufrufe und keine bezahlten APIs.
"""
import concurrent.futures
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_ollama as lokal
from ki import KINichtVerfuegbar
from test_local_ollama import gueltige_antwort


class TestMaster80Zaehlerintegritaet(unittest.TestCase):
    def setUp(self):
        # Offline unit fixture: consent is tested separately in approval suites.
        consent = mock.patch.object(lokal, "pruefe_freigabe", return_value="S-000")
        consent.start()
        self.addCleanup(consent.stop)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = pathlib.Path(temp.name)
        self.counter = self.root / "work" / "ki_aufrufe.txt"
        patch = mock.patch.dict(os.environ, {
            "SCHNAPPER_KI_BACKEND": "ollama",
            "SCHNAPPER_OLLAMA_MODELL": "qwen2.5:1.5b",
        })
        patch.start()
        self.addCleanup(patch.stop)
        self.ki = lokal.KI(self.counter)

    def test_neue_datei_erzeugt_reservierung_eins(self):
        self.assertEqual(self.ki._zaehle(), 1)
        self.assertEqual(self.counter.read_text(), "00000001")

    def test_mehrere_aufrufe_bleiben_eindeutig(self):
        self.assertEqual([self.ki._zaehle() for _ in range(3)], [1, 2, 3])
        self.assertEqual(int(self.counter.read_text()), 3)

    def test_legacy_einstelliger_zaehler_weiterhin_lesbar(self):
        self.counter.parent.mkdir()
        self.counter.write_text("3", encoding="ascii")
        self.assertEqual(self.ki._zaehle(), 4)
        self.assertEqual(self.counter.read_text(), "00000004")

    def test_gueltiges_limit_wird_streng_eingehalten(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 2):
            self.assertEqual(self.ki._zaehle(), 1)
            self.assertEqual(self.ki._zaehle(), 2)
            with self.assertRaisesRegex(KINichtVerfuegbar, "Maximal"):
                self.ki._zaehle()
            self.assertEqual(self.counter.read_text(), "00000002")

    def test_ungueltige_counterdaten_nicht_ueberschreiben(self):
        self.counter.parent.mkdir()
        for roh in ("broken", "1.0", "-1", "3\n", " 4", "999999999"):
            with self.subTest(roh=roh):
                self.counter.write_text(roh, encoding="ascii")
                with self.assertRaises(KINichtVerfuegbar):
                    self.ki._zaehle()
                self.assertEqual(self.counter.read_text(), roh)

    def test_symlink_auf_externe_datei_blockiert_ohne_schreiben(self):
        self.counter.parent.mkdir()
        fremd = self.root / "external.txt"
        fremd.write_text("3")
        self.counter.symlink_to(fremd)
        with self.assertRaises(KINichtVerfuegbar):
            self.ki._zaehle()
        self.assertEqual(fremd.read_text(), "3")

    def test_defekter_symlink_blockiert(self):
        self.counter.parent.mkdir()
        self.counter.symlink_to(self.root / "missing")
        with self.assertRaises(KINichtVerfuegbar):
            self.ki._zaehle()

    def test_verzeichnis_als_zaehler_blockiert(self):
        self.counter.mkdir(parents=True)
        with self.assertRaises(KINichtVerfuegbar):
            self.ki._zaehle()

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO auf POSIX erforderlich")
    def test_fifo_als_zaehler_blockiert_ohne_haenger(self):
        self.counter.parent.mkdir()
        os.mkfifo(self.counter)
        with self.assertRaises(KINichtVerfuegbar):
            self.ki._zaehle()

    def test_hardlink_auf_fremde_datei_blockiert(self):
        self.counter.parent.mkdir()
        fremd = self.root / "original.txt"
        fremd.write_text("2")
        os.link(fremd, self.counter)
        with self.assertRaises(KINichtVerfuegbar):
            self.ki._zaehle()
        self.assertEqual(fremd.read_text(), "2")

    def test_parallel_aufrufe_kein_doppeltes_inkrement(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 6):
            def arbeit(_):
                try:
                    return self.ki._zaehle()
                except KINichtVerfuegbar:
                    return None
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
                ergebnisse = list(pool.map(arbeit, range(12)))
        self.assertEqual(sorted(n for n in ergebnisse if n is not None),
                         [1, 2, 3, 4, 5, 6])
        self.assertEqual(ergebnisse.count(None), 6)
        self.assertEqual(int(self.counter.read_text()), 6)

    def test_antwort_nutzt_reservierte_nummer_statt_nachlesen(self):
        antwort = gueltige_antwort(
            model="qwen2.5:1.5b",
            message={"role": "assistant", "content": "Offline-Mock-Antwort"})
        def fake(pfad, payload=None, timeout=10):
            if pfad == "/api/tags":
                return {"models": [{"name": "qwen2.5:1.5b"}]}
            self.assertEqual(pfad, "/api/chat")
            return antwort
        with mock.patch.object(lokal, "_request", side_effect=fake):
            first = self.ki.frage("system", "frage1")
            second = self.ki.frage("system", "frage2")
        self.assertEqual((first["aufruf_nr"], second["aufruf_nr"]), (1, 2))
        self.assertEqual(int(self.counter.read_text()), 2)

    def test_fehlgeschlagene_antwort_reservierung_nicht_wiederverwenden(self):
        with mock.patch.object(lokal, "_request", side_effect=[
                {"models": [{"name": "qwen2.5:1.5b"}]},
                gueltige_antwort(model="qwen2.5:1.5b", message={"role": "assistant", "content": ""}),
        ]):
            with self.assertRaises(KINichtVerfuegbar):
                self.ki.frage("system", "frage")
        self.assertEqual(self.counter.read_text(), "00000001")

    def test_offline_zaehlerverwendung_hat_keinen_netzwerkzugriff(self):
        with mock.patch.object(lokal, "_request",
                               side_effect=AssertionError("network forbidden")):
            self.assertEqual(self.ki._zaehle(), 1)

    def test_kein_zugriff_bei_ungueltigem_backend(self):
        with mock.patch.dict(os.environ, {"SCHNAPPER_KI_BACKEND": "cloud"}):
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.counter)
        self.assertFalse(self.counter.exists())


if __name__ == "__main__":
    unittest.main()
