"""Kostenfreie lokale KI: Tests OHNE Modell-Download und OHNE Netzwerkanfrage."""
import os
import pathlib
import tempfile
import unittest
from unittest import mock

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "team"))
import local_ollama as lokal
from ki import KINichtVerfuegbar


class TestLokaleKI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.zaehler = pathlib.Path(self.temp.name) / "aufrufe.txt"
        self.env = mock.patch.dict(os.environ, {
            "SCHNAPPER_KI_BACKEND": "ollama",
            "SCHNAPPER_OLLAMA_MODELL": "qwen2.5:3b",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_keine_fremde_url_konfigurierbar(self):
        self.assertEqual(lokal.LOKAL, "http://127.0.0.1:11434")
        with mock.patch.dict(os.environ, {"OLLAMA_HOST": "https://fremder-host.example"}):
            self.assertEqual(lokal.LOKAL, "http://127.0.0.1:11434")
        with self.assertRaises(KINichtVerfuegbar):
            lokal._request("/api/pull")

    def test_weiterleitungen_verboten(self):
        handler = lokal.KeineWeiterleitungen()
        with self.assertRaises(KINichtVerfuegbar):
            handler.redirect_request(None, None, 302, "redirect",
                                     {}, "https://example.invalid/")

    def test_lokale_inferenz_und_zaehler(self):
        def fake(pfad, payload=None, timeout=10):
            if pfad == "/api/tags":
                return {"models": [{"name": "qwen2.5:3b"}]}
            self.assertEqual(pfad, "/api/chat")
            self.assertEqual(payload["model"], "qwen2.5:3b")
            self.assertFalse(payload["stream"])
            return {"message": {"content": "Echte Modellantwort nur im Produktivlauf."},
                    "prompt_eval_count": 12, "eval_count": 4}

        with mock.patch.object(lokal, "_request", side_effect=fake):
            ki = lokal.KI(self.zaehler)
            result = ki.frage("System", "Frage")
        self.assertEqual(result["laufzeit"], "Ollama lokal (keine bezahlte KI-API)")
        self.assertEqual(result["modell"], "qwen2.5:3b")
        self.assertEqual(result["aufruf_nr"], 1)
        self.assertEqual(int(self.zaehler.read_text()), 1)

    def test_fehlendes_modell_wird_nicht_ersetzt(self):
        with mock.patch.object(lokal, "_request",
                               return_value={"models": [{"name": "anderes:1b"}]}):
            with self.assertRaisesRegex(KINichtVerfuegbar, "nicht installiert"):
                lokal.KI(self.zaehler).frage("S", "N")
        self.assertFalse(self.zaehler.exists())

    def test_keine_rueckkehr_zu_bezahl_api(self):
        with mock.patch.dict(os.environ, {"SCHNAPPER_KI_BACKEND": "github"}):
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.zaehler)

    def test_lokales_limit(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 1), \
             mock.patch.object(lokal, "_request", side_effect=[
                 {"models": [{"name": "qwen2.5:3b"}]},
                 {"message": {"content": "eins"}},
                 {"models": [{"name": "qwen2.5:3b"}]},
             ]):
            ki = lokal.KI(self.zaehler)
            ki.frage("s", "n")
            with self.assertRaisesRegex(KINichtVerfuegbar, "Maximal"):
                ki.frage("s", "n")


if __name__ == "__main__":
    unittest.main()
