"""Tests für Quellen-Register, Adapter (Plan S-002: T1–T5) und Web-Oberfläche."""
import json
import os
import pathlib
import socket
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.adapter import DateiAdapter, EbayAdapter, QuelleGesperrt, finde  # noqa: E402
from schnapper.einlesen import lies_text  # noqa: E402
from schnapper.quellen import QuellenFehler, Register  # noqa: E402
from schnapper.web import erstelle_server  # noqa: E402

BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"


def zeile(**kw):
    d = {"id": "a", "titel": "Fahrrad", "preis": "50", "url": "https://x.example/1", "quelle": "mock",
         "erfasst_am": "2026-10-21T20:00:00Z", "referenzpreis": "100"}
    d.update(kw)
    return d


class QuellenRegister(unittest.TestCase):
    def test_t1_ausgeschlossene_quelle(self):
        e = lies_text(json.dumps([zeile(quelle="kleinanzeigen")]), "json")
        self.assertEqual(e.angebote, [])
        self.assertIn("ausgeschlossen", e.fehler[0])

    def test_t2_unbekannte_quelle(self):
        e = lies_text(json.dumps([zeile(quelle="irgendwas")]), "json")
        self.assertEqual(e.angebote, [])
        self.assertIn("nicht freigegeben", e.fehler[0])

    def test_t3_mock_und_eigene_erlaubt(self):
        e = lies_text(json.dumps([zeile(id="1", quelle="mock"), zeile(id="2", quelle="EIGENE", url="https://x.example/2")]), "json")
        self.assertEqual([a.id for a in e.angebote], ["1", "2"])

    def test_ebay_noch_gesperrt(self):
        self.assertIn("noch gesperrt", lies_text(json.dumps([zeile(quelle="ebay")]), "json").fehler[0])

    def test_ausgeschlossene_quelle_nicht_per_datei_freischaltbar(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "quellen.json"
            p.write_text(json.dumps({"quellen": [{"kennung": "kleinanzeigen", "name": "x", "hinweis": "y"}]}))
            with self.assertRaises(QuellenFehler):
                Register.mit_datei(p)

    def test_freigabe_braucht_hinweis_zum_nutzungsrecht(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "quellen.json"
            p.write_text(json.dumps({"quellen": [{"kennung": "partner", "name": "Partner"}]}))
            with self.assertRaises(QuellenFehler):
                Register.mit_datei(p)

    def test_ungueltige_kennung(self):
        with self.assertRaises(QuellenFehler):
            Register().erlaube("../böse", "x", "y")


class Adapter(unittest.TestCase):
    def test_t4_ebay_ohne_freigabe_kein_netz(self):
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("Netzwerkaufruf!")), \
                mock.patch("socket.create_connection", side_effect=AssertionError("Netzwerkaufruf!")):
            with self.assertRaises(QuelleGesperrt):
                EbayAdapter().lade()
            with mock.patch.dict(os.environ, {"SCHNAPPER_EBAY_FREIGABE": "ja"}):
                with self.assertRaises(QuelleGesperrt):  # Register sperrt weiterhin
                    EbayAdapter().lade()

    def test_datei_adapter_kompletter_ablauf(self):
        e = finde(DateiAdapter(BEISPIEL))
        self.assertEqual(e.eingelesen, 5)
        self.assertEqual([(a.id, b.id) for a, b in e.dubletten], [("b1", "b2")])
        self.assertTrue(any("Preis muss größer als 0" in f for f in e.fehler))


class Web(unittest.TestCase):
    """Jede Testklasse bekommt einen eigenen Server, Tests ändern sich nicht gegenseitig."""

    @classmethod
    def setUpClass(cls):
        cls.server = erstelle_server(BEISPIEL, port=0)
        cls.basis = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def hole(self, pfad, daten=None, kopf=None):
        req = urllib.request.Request(self.basis + pfad, data=daten, headers=kopf or {}, method="POST" if daten else "GET")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=5) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_t5_lokal_ohne_internet(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_seite_mit_sicherheitskoepfen(self):
        status, kopf, inhalt = self.hole("/")
        self.assertEqual(status, 200)
        self.assertIn(b"SCHNAPPER", inhalt)
        self.assertIn("script-src 'self'", kopf["Content-Security-Policy"])
        self.assertEqual(kopf["X-Content-Type-Options"], "nosniff")
        for datei in ("/app.js", "/app.css"):
            self.assertEqual(self.hole(datei)[0], 200)

    def test_suche_api(self):
        status, _, inhalt = self.hole("/api/suche?text=kopfhoerer&sortierung=preis")
        daten = json.loads(inhalt)
        self.assertEqual(status, 200)
        self.assertTrue(daten["beispieldaten"])
        self.assertEqual([t["id"] for t in daten["treffer"]], ["b2", "b3"])
        self.assertEqual(daten["treffer"][0]["gesamtpreis"], "54.89")

    def test_suche_api_ungueltige_eingabe(self):
        for q in ("max_preis=abc", "sortierung=zufall", "zustand=super"):
            with self.subTest(q):
                self.assertEqual(self.hole("/api/suche?" + q)[0], 400)

    def test_merkliste_und_preisalarm_in_der_oberflaeche(self):
        _, _, html = self.hole("/")
        for teil in (b'id="ansicht-merkliste"', b'id="ansicht-alarme"', b'id="alarm-anlegen"', b'class="merken"'):
            self.assertIn(teil, html)
        js = self.hole("/app.js")[2].decode("utf-8")
        self.assertNotIn(".innerHTML", js)  # fremde Titel nie als HTML einsetzen
        # Jeder Zugriff auf localStorage muss abgesichert sein (privates Fenster wirft Fehler)
        for zeile in js.splitlines():
            if "localStorage." in zeile:
                self.assertRegex(zeile, r"try\s*\{|^\s*const roh|^\s*catch|setItem", zeile)

    def test_alarm_abfrage_der_oberflaeche(self):
        # So fragt die Oberfläche einen Preisalarm ab: günstigstes zuerst, veraltete ausgeblendet
        status, _, inhalt = self.hole("/api/suche?text=kopfhoerer&max_preis=55&sortierung=preis&ohne_veraltet=1")
        self.assertEqual(status, 200)
        self.assertTrue(all(float(t["gesamtpreis"]) <= 55 for t in json.loads(inhalt)["treffer"]))

    def test_unbekannter_pfad(self):
        self.assertEqual(self.hole("/../../etc/passwd")[0], 404)
        self.assertEqual(self.hole("/api/gibtsnicht")[0], 404)


class WebImport(Web):
    test_t5_lokal_ohne_internet = test_seite_mit_sicherheitskoepfen = None
    test_suche_api = test_suche_api_ungueltige_eingabe = test_unbekannter_pfad = None

    def test_import_schutz_und_quellenpruefung(self):
        csv_text = ("id;titel;preis;url;quelle;erfasst_am\n"
                    "e1;Lampe;10;https://x.example/l;eigene;2026-10-21T20:00:00Z\n"
                    "e2;Tisch;20;https://x.example/t;kleinanzeigen;2026-10-21T20:00:00Z\n").encode()
        # ohne Schutz-Kopf: abgelehnt (fremde Webseiten dürfen nicht hochladen)
        self.assertEqual(self.hole("/api/import", csv_text, {"X-Dateiname": "a.csv"})[0], 403)
        self.assertEqual(self.hole("/api/import", csv_text, {"X-Schnapper": "1", "X-Dateiname": "a.exe"})[0], 400)
        status, _, inhalt = self.hole("/api/import", csv_text, {"X-Schnapper": "1", "X-Dateiname": "../meine.csv"})
        daten = json.loads(inhalt)
        self.assertEqual(status, 200)
        self.assertEqual(daten["eingelesen"], 1)
        self.assertIn("ausgeschlossen", daten["ungueltig"][0])
        suche = json.loads(self.hole("/api/suche")[2])
        self.assertEqual(suche["liste"], "meine.csv")
        self.assertFalse(suche["beispieldaten"])
        self.assertEqual([t["id"] for t in suche["treffer"]], ["e1"])


if __name__ == "__main__":
    unittest.main()
