"""SCHNAPPER: direkte Einzel-Erfassung im lokalen Webserver testen.

Echte localhost-HTTP-Aufrufe; keine Abfrage irgendeines Marktplatzes.
"""
import csv
import io
import json
import pathlib
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.verlauf import Verlauf  # noqa: E402
from schnapper.web import erstelle_server  # noqa: E402

HEADER = "id;titel;preis;versand;referenzpreis;zustand;quelle;kategorie;url;erfasst_am"
START = ("alt;Kopfhörer;50;5;80;gebraucht;eigene;Audio;"
         "https://shop.example/start;2026-10-21T11:00:00Z")


class LokaleErfassung(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        pfad = pathlib.Path(self.temp.name) / "eigene.csv"
        pfad.write_text(HEADER + "\n" + START + "\n", encoding="utf-8")
        self.verlauf = pathlib.Path(self.temp.name) / "verlauf.json"
        self.server = erstelle_server(pfad, port=0, verlauf=self.verlauf)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def http(self, path, payload=None, headers=None, method=None):
        req = urllib.request.Request(self.base + path, data=payload, headers=headers or {},
                                     method=method or ("POST" if payload is not None else "GET"))
        try:
            with self.opener.open(req, timeout=5) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def eintrag(self, **andere):
        wert = {"titel": "Schnäppchen Kopfhörer", "preis": "40,00",
                "versand": "5", "referenzpreis": "85",
                "zustand": "gebraucht", "kategorie": "Audio",
                "url": "https://shop.example/eigenes"}
        wert.update(andere)
        return wert

    def sende(self, wert="__DEFAULT__", headers=None):
        return self.http("/api/eigenes-angebot", json.dumps(
            self.eintrag() if wert == "__DEFAULT__" else wert, ensure_ascii=False).encode("utf-8"),
            headers if headers is not None else {
                "X-Schnapper": "1", "Content-Type": "application/json"})

    def suche(self, query=""):
        code, _, body = self.http("/api/suche" + query)
        self.assertEqual(code, 200)
        return json.loads(body)

    def test_eigenes_angebot_ist_sofort_in_suche_und_export(self):
        code, headers, body = self.sende()
        self.assertEqual(code, 201)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(json.loads(body)["quelle"], "eigene")
        self.assertTrue(json.loads(body)["hinzugefuegt"].startswith("eigene-"))
        eintraege = self.suche("?quelle=eigene&kategorie=Audio&sortierung=preis")["treffer"]
        self.assertEqual(len(eintraege), 2)
        manuell = eintraege[0]
        self.assertEqual(manuell["titel"], "Schnäppchen Kopfhörer")
        self.assertEqual(manuell["gesamtpreis"], "45.00")
        self.assertEqual(manuell["referenzpreis"], "85.00")
        self.assertEqual(manuell["quelle"], "eigene")
        self.assertTrue(manuell["id"].startswith("eigene-"))
        code, _, body = self.http("/api/export.csv?max_preis=45&quelle=eigene")
        self.assertEqual(code, 200)
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], manuell["id"])

    def test_beliebige_fremde_quelle_id_und_zeitpunkt_werden_ignoriert(self):
        data = self.eintrag(quelle="kleinanzeigen", id="fremd",
                           erfasst_am="2000-01-01T00:00:00Z")
        code, _, raw = self.sende(data)
        self.assertEqual(code, 201)
        result = json.loads(raw)
        self.assertEqual(result["quelle"], "eigene")
        self.assertNotEqual(result["hinzugefuegt"], "fremd")
        t = self.suche("?quelle=eigene&kategorie=Audio")["treffer"]
        neu = [x for x in t if x["id"] != "alt"]
        self.assertEqual(len(neu), 1)
        self.assertTrue(neu[0]["erfasst_am"].startswith("2026-"))
        self.assertEqual(self.suche("?quelle=kleinanzeigen")["treffer"], [])

    def test_gleicher_link_mit_tracking_wird_abgewiesen(self):
        code, _, raw = self.sende(self.eintrag(
            url="https://shop.example/start?utm_source=test&fbclid=abc"))
        self.assertEqual(code, 409)
        self.assertIn("bereits", json.loads(raw)["fehler"])
        self.assertEqual(len(self.suche()["treffer"]), 1)

    def test_zweimaliges_absenden_schreibt_keine_dublette(self):
        self.assertEqual(self.sende()[0], 201)
        code, _, _ = self.sende()
        self.assertEqual(code, 409)
        self.assertEqual(len(self.suche()["treffer"]), 2)

    def test_fehlende_header_falscher_medientyp_grosses_json(self):
        self.assertEqual(self.sende(headers={"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.sende(headers={
            "X-Schnapper": "1", "Content-Type": "text/plain"})[0], 415)
        zu_gross = json.dumps(self.eintrag(titel="a" * 5000)).encode("utf-8")
        code, _, _ = self.http("/api/eigenes-angebot", zu_gross, {
            "X-Schnapper": "1", "Content-Type": "application/json"})
        self.assertEqual(code, 413)
        code, _, _ = self.http("/api/eigenes-angebot", b"keine json daten", {
            "X-Schnapper": "1", "Content-Type": "application/json"})
        self.assertEqual(code, 400)
        self.assertEqual(self.suche()["eingelesen"], 1)

    def test_keine_json_objekte_werden_akzeptiert(self):
        for wert in ([], "x", None, 23):
            with self.subTest(wert=wert):
                code, _, _ = self.sende(wert)
                self.assertEqual(code, 400)
        self.assertEqual(self.suche()["eingelesen"], 1)

    def test_invalides_angebot_wird_nicht_gespeichert(self):
        faelle = (
            self.eintrag(preis="0"),
            self.eintrag(preis="NaN"),
            self.eintrag(versand="-1"),
            self.eintrag(referenzpreis="-1"),
            self.eintrag(url="http://shop.example/item"),
            self.eintrag(url="https://user:pass@shop.example/secret"),
            self.eintrag(zustand="unbekannt-gefälscht"),
            self.eintrag(kategorie="x" * 81),
            self.eintrag(titel="x" * 301),
            self.eintrag(titel=""),
        )
        for wert in faelle:
            with self.subTest(wert=wert):
                code, _, body = self.sende(wert)
                self.assertEqual(code, 400)
                self.assertIn("fehler", json.loads(body))
        self.assertEqual(self.suche()["eingelesen"], 1)

    def test_speicherfehler_laesst_die_liste_unveraendert(self):
        vorher = self.verlauf.read_bytes()
        with mock.patch.object(Verlauf, "importiere", side_effect=OSError("simuliert")):
            code, _, raw = self.sende()
        self.assertEqual(code, 500)
        self.assertIn("nicht gespeichert", json.loads(raw)["fehler"])
        self.assertEqual(len(self.suche()["treffer"]), 1)
        self.assertEqual(self.verlauf.read_bytes(), vorher)

    def test_hoechstanzahl_begrenzt_und_ohne_veraenderung(self):
        with mock.patch("schnapper.web.MAX_ANGEBOTE", 1):
            code, _, raw = self.sende()
        self.assertEqual(code, 409)
        self.assertIn("Maximal", json.loads(raw)["fehler"])
        self.assertEqual(self.suche()["eingelesen"], 1)

    def test_gleichzeitige_gleiche_eingaben_nur_einmal_gespeichert(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(lambda _: self.sende()[0], range(2)))
        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(self.suche()["eingelesen"], 2)

    def test_webformular_und_javascript_sind_ausgeliefert(self):
        code, _, html = self.http("/")
        self.assertEqual(code, 200)
        self.assertIn(b'id="eintrag-form"', html)
        self.assertIn(b'name="titel"', html)
        self.assertIn(b'name="preis"', html)
        self.assertIn(b'name="url"', html)
        self.assertIn(b'name="referenzpreis"', html)
        self.assertIn(b"Nur eigene Fundst", html)
        code, _, js = self.http("/app.js")
        self.assertEqual(code, 200)
        self.assertIn(b"/api/eigenes-angebot", js)
        self.assertIn(b'$("eintrag-form").addEventListener("submit", eigenesAngebotErfassen)', js)
        self.assertNotIn(b".innerHTML", js)

    def test_get_eintrag_und_ungueltiger_post_pfaden_ist_nicht_zulaessig(self):
        self.assertEqual(self.http("/api/eigenes-angebot")[0], 404)
        code, _, _ = self.http("/api/unbekannt", b"{}", {
            "X-Schnapper": "1", "Content-Type": "application/json"})
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
