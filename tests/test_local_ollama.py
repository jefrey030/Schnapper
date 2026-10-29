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



def gueltige_antwort(**aenderungen):
    """Nur synthetische Ollama-JSON-Fixture, kein echter Modellaufruf."""
    basis = {
        "model": "qwen2.5:3b",
        "created_at": "2026-10-25T13:00:00Z",
        "message": {"role": "assistant", "content": "Testtext"},
        "done": True, "done_reason": "stop",
        "prompt_eval_count": 12, "eval_count": 4,
    }
    basis.update(aenderungen)
    return basis


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
        # This fixture simulates downstream Ollama behavior under approved conditions;
        # separate MASTER 121 tests prove that real unapproved requests are denied.
        consent = mock.patch.object(lokal, "pruefe_freigabe", return_value="S-014")
        consent.start()
        self.addCleanup(consent.stop)

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
            return gueltige_antwort(message={"role": "assistant", "content": "Nur Mock-Daten."})

        with mock.patch.object(lokal, "_request", side_effect=fake):
            ki = lokal.KI(self.zaehler)
            result = ki.frage("System", "Frage")
        self.assertEqual(result["laufzeit"], "Ollama lokal (keine bezahlte KI-API)")
        self.assertEqual(result["modell"], "qwen2.5:3b")
        self.assertEqual(result["aufruf_nr"], 1)
        self.assertEqual(result["antwort_id_typ"], "nur-lokale-kennung")
        self.assertEqual(result["ollama_beleg"]["modell_antwort"], "qwen2.5:3b")
        self.assertEqual(result["ollama_beleg"]["eval_count"], 4)
        self.assertEqual(int(self.zaehler.read_text()), 1)


    def test_fehlerhafte_providerdaten_bleiben_gesperrt(self):
        ungueltige = [
            ("kein Dict", ["antwort"], "Antworttyp"),
            ("anderes Modell", gueltige_antwort(model="anderes:9b"), "unerwartetes Modell"),
            ("nur Fragment", gueltige_antwort(done=False), "nicht vollständig"),
            ("kein Stop", gueltige_antwort(done_reason="length"), "nicht vollständig"),
            ("falsche Rolle", gueltige_antwort(message={"role": "user", "content": "x"}), "Assistant-Rolle"),
            ("kein Inhalt", gueltige_antwort(message={"role": "assistant", "content": ""}), "Leere"),
            ("fehlendes Datum", gueltige_antwort(created_at=None), "Zeitstempel"),
            ("ungültiges Datum", gueltige_antwort(created_at="gestern"), "Zeitstempel"),
            ("kein Tokenzähler", gueltige_antwort(eval_count=None), "Tokenzählung"),
            ("bool statt Anzahl", gueltige_antwort(eval_count=True), "Tokenzählung"),
            ("null erzeugt", gueltige_antwort(eval_count=0), "Tokenzählung"),
        ]
        for name, antwort, fehlertext in ungueltige:
            with self.subTest(name=name), mock.patch.object(lokal, "_request", side_effect=[
                {"models": [{"name": "qwen2.5:3b"}]}, antwort,
            ]):
                self.zaehler.unlink(missing_ok=True)
                with self.assertRaisesRegex(KINichtVerfuegbar, fehlertext):
                    lokal.KI(self.zaehler).frage("System", "Test")
                self.assertEqual(int(self.zaehler.read_text()), 1)

    def test_fehlformatierte_katalogeintraege_blockieren_ohne_absturz(self):
        with mock.patch.object(lokal, "_request", return_value={
            "models": [{"name": {"dict": "kein Name"}}, {"name": ["liste"]}]
        }):
            with self.assertRaisesRegex(KINichtVerfuegbar, "nicht installiert"):
                lokal.KI(self.zaehler).frage("S", "N")
        self.assertFalse(self.zaehler.exists())

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


    def test_cloud_modelle_auch_ueber_localhost_verboten(self):
        with mock.patch.dict(os.environ, {
            "SCHNAPPER_OLLAMA_MODELL": "gemma4:cloud"
        }):
            with self.assertRaisesRegex(KINichtVerfuegbar, "Cloud-Modelle"):
                lokal.KI(self.zaehler)
        self.assertFalse(self.zaehler.exists())

    def test_lokales_limit(self):
        with mock.patch.object(lokal, "MAX_AUFRUFE", 1), \
             mock.patch.object(lokal, "_request", side_effect=[
                 {"models": [{"name": "qwen2.5:3b"}]},
                 gueltige_antwort(),
                 {"models": [{"name": "qwen2.5:3b"}]},
             ]):
            ki = lokal.KI(self.zaehler)
            ki.frage("s", "n")
            with self.assertRaisesRegex(KINichtVerfuegbar, "Maximal"):
                ki.frage("s", "n")


if __name__ == "__main__":
    unittest.main()
