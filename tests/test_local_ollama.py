"""Kostenfreie lokale KI: Tests OHNE Modell-Download und OHNE Netzwerkanfrage."""
import os
import pathlib
import tempfile
import threading
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


    def test_cloud_modelle_auch_ueber_localhost_verboten(self):
        with mock.patch.dict(os.environ, {
            "SCHNAPPER_OLLAMA_MODELL": "gemma4:cloud"
        }):
            with self.assertRaisesRegex(KINichtVerfuegbar, "Cloud-Modelle"):
                lokal.KI(self.zaehler)
        self.assertFalse(self.zaehler.exists())

    def test_api_antwort_ohne_json_objekt_wird_blockiert(self):
        # HTTP-Aufruf vollständig gemockt, keine reale Ollama-Verbindung.
        for raw in (b"[]", b"null", b"42", b'"test"'):
            with self.subTest(raw=raw), mock.patch.object(lokal._HTTP, "open") as opener:
                opener.return_value.__enter__.return_value.read.return_value = raw
                with self.assertRaisesRegex(KINichtVerfuegbar, "JSON-Objekt"):
                    lokal._request("/api/tags")
                self.assertEqual(opener.call_count, 1)

    def test_kaputte_modellliste_ohne_modellaufruf_blockiert(self):
        faelle = (
            {"models": [{"name": ["qwen2.5:3b"]}]},
            {"models": [{"name": {"nested": "qwen2.5:3b"}}]},
            {"models": [None, 42, {"name": None}]},
            {"models": "kein array"},
            {"models": None},
            [],
        )
        for katalog in faelle:
            with self.subTest(katalog=katalog):
                self.zaehler.unlink(missing_ok=True)
                with mock.patch.object(lokal, "_request", return_value=katalog) as req:
                    with self.assertRaises(KINichtVerfuegbar):
                        lokal.KI(self.zaehler).frage("s", "n")
                    req.assert_called_once_with("/api/tags")
                self.assertFalse(self.zaehler.exists())

    def test_negative_oder_beschaedigte_zaehler_blockieren_chat(self):
        for wert in ("-1", "10000", "kaputt", "1" * 50, ""):
            with self.subTest(wert=wert):
                self.zaehler.write_text(wert, encoding="utf-8")
                with mock.patch.object(lokal, "_request",
                                       return_value={"models": [{"name": "qwen2.5:3b"}]}) as req:
                    with self.assertRaises(KINichtVerfuegbar):
                        lokal.KI(self.zaehler).frage("s", "n")
                    req.assert_called_once_with("/api/tags")

    def test_ueberhoehtes_und_unmoegliches_limit_werden_blockiert(self):
        for limit in (0, -1, 7, 99999, True):
            with self.subTest(limit=limit), mock.patch.object(lokal, "MAX_AUFRUFE", limit), \
                 mock.patch.object(lokal, "_request",
                                   return_value={"models": [{"name": "qwen2.5:3b"}]}) as req:
                self.zaehler.unlink(missing_ok=True)
                with self.assertRaises(KINichtVerfuegbar):
                    lokal.KI(self.zaehler).frage("s", "n")
                req.assert_called_once_with("/api/tags")
                self.assertFalse(self.zaehler.exists())

    def test_symbolischer_zaehler_wird_nicht_ueberschrieben(self):
        target = self.zaehler.with_name("fremd.txt")
        target.write_text("0", encoding="utf-8")
        try:
            self.zaehler.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink hier nicht verfügbar")
        with mock.patch.object(lokal, "_request",
                               return_value={"models": [{"name": "qwen2.5:3b"}]}) as req:
            with self.assertRaises(KINichtVerfuegbar):
                lokal.KI(self.zaehler).frage("s", "n")
            req.assert_called_once_with("/api/tags")
        self.assertEqual(target.read_text(encoding="utf-8"), "0")

    def test_leere_falsche_oder_zu_grosse_modellantwort_gesperrt(self):
        faelle = (
            {}, {"message": None}, {"message": {"content": None}},
            {"message": {"content": ["kein text"]}},
            {"message": {"content": "  "}},
            {"message": {"content": "a" * 12001}},
            [],
        )
        for antwort in faelle:
            with self.subTest(antworttyp=type(antwort).__name__,
                              fall=str(antwort)[:20]):
                self.zaehler.unlink(missing_ok=True)
                with mock.patch.object(lokal, "_request", side_effect=[
                    {"models": [{"name": "qwen2.5:3b"}]},
                    antwort,
                ]) as req:
                    with self.assertRaises(KINichtVerfuegbar):
                        lokal.KI(self.zaehler).frage("s", "n")
                    self.assertEqual(req.call_count, 2)
                # Auch der missglückte Chatversuch verbraucht sein Kontingent.
                self.assertEqual(self.zaehler.read_text(encoding="utf-8"), "1")

    def test_sperre_verhindert_parallele_zaehlung(self):
        # Simuliert zwei konkurrierende Aufrufer ohne einen Chat-/HTTP-Aufruf.
        ki = lokal.KI(self.zaehler)
        start = threading.Event()
        freigabe = threading.Event()
        ergebnisse = []
        original = pathlib.Path.write_text

        def langsam(pfad, inhalt, *args, **kwargs):
            if pfad == self.zaehler:
                start.set()
                if not freigabe.wait(timeout=5):
                    raise OSError("Nur Test: Schreibvorgang nicht freigegeben")
            return original(pfad, inhalt, *args, **kwargs)

        def erster():
            try:
                ergebnisse.append(ki._zaehle())
            except Exception as exc:
                ergebnisse.append(exc)

        with mock.patch.object(pathlib.Path, "write_text", new=langsam):
            prozess = threading.Thread(target=erster, daemon=True)
            prozess.start()
            try:
                self.assertTrue(start.wait(timeout=5))
                with self.assertRaisesRegex(KINichtVerfuegbar, "gesperrt"):
                    ki._zaehle()
            finally:
                freigabe.set()
                prozess.join(timeout=5)
        self.assertFalse(prozess.is_alive())
        self.assertEqual(ergebnisse, [1])
        self.assertEqual(self.zaehler.read_text(encoding="utf-8"), "1")
        self.assertEqual(ki._zaehle(), 2)

    def test_verwaister_lock_blockiert_statt_zu_ueberschreiben(self):
        sperre = self.zaehler.with_name(self.zaehler.name + ".lock")
        sperre.mkdir()
        ki = lokal.KI(self.zaehler)
        with self.assertRaisesRegex(KINichtVerfuegbar, "verwaister"):
            ki._zaehle()
        self.assertTrue(sperre.is_dir())
        self.assertFalse(self.zaehler.exists())

    def test_fehlerhaftes_counter_schreiben_raeumt_lock_auf(self):
        ki = lokal.KI(self.zaehler)
        with mock.patch.object(pathlib.Path, "write_text",
                               side_effect=OSError("simulierter Defekt")):
            with self.assertRaises(KINichtVerfuegbar):
                ki._zaehle()
        sperre = self.zaehler.with_name(self.zaehler.name + ".lock")
        self.assertFalse(sperre.exists())
        # Nach Behebung des künstlichen Problems wieder genau ein Versuch.
        self.assertEqual(ki._zaehle(), 1)

    def test_limit_abgelehnt_ohne_lock_zu_hinterlassen(self):
        ki = lokal.KI(self.zaehler)
        self.zaehler.write_text(str(lokal.MAX_AUFRUFE), encoding="utf-8")
        with self.assertRaisesRegex(KINichtVerfuegbar, "Maximal"):
            ki._zaehle()
        self.assertFalse(self.zaehler.with_name(
            self.zaehler.name + ".lock").exists())
        self.assertEqual(int(self.zaehler.read_text()), lokal.MAX_AUFRUFE)

    def test_aufrufnummer_wird_aus_reservierung_uebernommen(self):
        ki = lokal.KI(self.zaehler)
        def antwort(pfad, *args, **kwargs):
            if pfad == "/api/tags":
                return {"models": [{"name": "qwen2.5:3b"}]}
            if pfad == "/api/chat":
                # Externe Dateiveränderungen nach Reservierung dürfen die
                # belegte Versuchsnummer nicht nachträglich umetikettieren.
                self.zaehler.write_text("3", encoding="utf-8")
                return {"message": {"content": "Mock-Antwort"}}
            raise AssertionError("Unbekannter Testpfad")

        with mock.patch.object(lokal, "_request", side_effect=antwort):
            self.assertEqual(ki.frage("System", "Nutzer")["aufruf_nr"], 1)

    def test_blockierte_entfernung_des_locks_ist_fehler(self):
        ki = lokal.KI(self.zaehler)
        with mock.patch.object(pathlib.Path, "rmdir",
                               side_effect=OSError("Sperre noch in Benutzung")):
            with self.assertRaisesRegex(KINichtVerfuegbar, "nicht aufgehoben"):
                ki._zaehle()
        # Lock bleibt absichtlich stehen: keine unkontrollierte Wiederholung.
        sperre = self.zaehler.with_name(self.zaehler.name + ".lock")
        self.assertTrue(sperre.exists())
        with self.assertRaisesRegex(KINichtVerfuegbar, "gesperrt"):
            ki._zaehle()

    def test_symlink_oder_datei_als_lock_bleibt_gesperrt(self):
        for art in ("file", "symlink"):
            with self.subTest(art=art):
                sperre = self.zaehler.with_name(self.zaehler.name + ".lock")
                ziel = self.zaehler.with_name("fremde-sperre.txt")
                ziel.write_text("geschützt", encoding="utf-8")
                if art == "file":
                    sperre.write_text("belegt", encoding="utf-8")
                else:
                    try:
                        sperre.symlink_to(ziel)
                    except (OSError, NotImplementedError):
                        self.skipTest("Symlinks nicht verfügbar")
                try:
                    with self.assertRaisesRegex(KINichtVerfuegbar, "gesperrt"):
                        lokal.KI(self.zaehler)._zaehle()
                    self.assertFalse(self.zaehler.exists())
                    self.assertEqual(ziel.read_text(encoding="utf-8"), "geschützt")
                finally:
                    sperre.unlink(missing_ok=True)

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
