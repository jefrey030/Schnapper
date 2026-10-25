"""Fertigstellungsabnahme: Quelle, Kategorie, Alarm und Export im Offline-MVP.

Alle HTTP-Aufrufe gehen an einen echten lokalen Testserver (127.0.0.1).
Keine externe Angebotsquelle, kein Modell, kein Download und keine Bezahl-API.
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
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.web import CSV_FELDER, erstelle_server, filter_aus_query  # noqa: E402

HEADER = "id;titel;preis;versand;referenzpreis;zustand;quelle;kategorie;url;erfasst_am"
ANGEBOTE = [
    "audio1;Kopfhörer Berlin;30;5;80;gebraucht;eigene;Audio;https://shop.example/audio1;2026-10-21T11:00:00Z",
    "audio2;Lautsprecher TEST;55;0;85;gebraucht;mock;Audio;https://example.invalid/audio2;2026-10-21T11:00:00Z",
    "rad1;Fahrrad Berlin;75;10;200;gebraucht;eigene;Fahrrad;https://shop.example/rad1;2026-10-21T11:00:00Z",
    "verboten;Fremde Quelle;1;0;80;gebraucht;kleinanzeigen;Audio;https://shop.example/verboten;2026-10-21T11:00:00Z",
]


class FilterValidierung(unittest.TestCase):
    def test_backend_uebernimmt_und_normalisiert_beide_filter(self):
        f, sortierung = filter_aus_query({
            "quelle": ["  EiGeNe  "],
            "kategorie": ["  aUdIo  "],
            "sortierung": ["preis"],
        })
        self.assertEqual(f.quellen, {"EiGeNe"})
        self.assertEqual(f.kategorie, "aUdIo")
        self.assertEqual(sortierung, "preis")

    def test_zu_lange_filter_werden_abgewiesen(self):
        for name in ("quelle", "kategorie"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "zu lang"):
                filter_aus_query({name: ["x" * 81]})


class FilterWebEndToEnd(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "eigene.csv"
        self.path.write_text(HEADER + "\n" + "\n".join(ANGEBOTE) + "\n", encoding="utf-8")
        self.server = erstelle_server(self.path, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = "http://127.0.0.1:" + str(self.server.server_address[1])
        self.client = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def get(self, path):
        req = urllib.request.Request(self.base + path)
        try:
            with self.client.open(req, timeout=5) as res:
                return res.status, res.headers, res.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def ids(self, path):
        status, headers, body = self.get(path)
        self.assertEqual(status, 200)
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        return [x["id"] for x in json.loads(body)["treffer"]]

    def test_nur_bekannte_quellen_und_kategorien_werden_gezeigt(self):
        self.assertEqual(set(self.ids("/api/suche?sortierung=preis")), {"audio1", "audio2", "rad1"})
        self.assertEqual(set(self.ids("/api/suche?kategorie=Audio")), {"audio1", "audio2"})
        self.assertEqual(set(self.ids("/api/suche?quelle=eigene")), {"audio1", "rad1"})
        self.assertEqual(self.ids("/api/suche?quelle=MOCK"), ["audio2"])

    def test_kombinierte_filter_und_gross_kleinschreibung(self):
        self.assertEqual(
            self.ids("/api/suche?quelle=EiGeNe&kategorie=aUdIo&max_preis=35&sortierung=preis"),
            ["audio1"],
        )
        self.assertEqual(self.ids("/api/suche?quelle=mock&kategorie=Fahrrad"), [])
        self.assertEqual(self.ids("/api/suche?quelle=kleinanzeigen"), [])
        self.assertEqual(self.ids("/api/suche?kategorie=unbekannt"), [])

    def test_csv_export_enthaelt_nur_genau_gefilterte_angebote(self):
        query = "?kategorie=Audio&quelle=eigene&sortierung=preis"
        status, headers, body = self.get("/api/export.csv" + query)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertTrue(body.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual([row["id"] for row in rows], ["audio1"])
        self.assertEqual(rows[0]["kategorie"], "Audio")
        self.assertEqual(rows[0]["quelle"], "eigene")
        self.assertEqual(rows[0]["gesamtpreis"], "35.00")
        self.assertEqual(rows[0]["referenzpreis"], "80.00")

    def test_json_export_ist_mit_suche_identisch(self):
        q = "?quelle=MoCk&kategorie=AuDiO&sortierung=preis"
        code, _, raw = self.get("/api/suche" + q)
        self.assertEqual(code, 200)
        code, headers, export = self.get("/api/export.json" + q)
        self.assertEqual(code, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        self.assertEqual(json.loads(raw), json.loads(export))
        self.assertEqual([r["id"] for r in json.loads(export)["treffer"]], ["audio2"])

    def test_kaputte_oder_ueberlange_filter_fehlern_bei_suche_und_export(self):
        for route in ("/api/suche", "/api/export.csv", "/api/export.json"):
            for feld in ("quelle", "kategorie"):
                q = urllib.parse.urlencode({feld: "x" * 81})
                with self.subTest(route=route, feld=feld):
                    code, headers, payload = self.get(route + "?" + q)
                    self.assertEqual(code, 400)
                    self.assertNotIn("Content-Disposition", headers)
                    self.assertIn("fehler", json.loads(payload))

    def test_leerer_treffer_export_hat_nur_header(self):
        status, _, payload = self.get("/api/export.csv?quelle=unknown&kategorie=Audio")
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(payload.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(rows, [list(CSV_FELDER)])

    def test_browser_zeigt_filter_und_preisalarme_folgen_ihnen(self):
        code, _, html = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn(b'id="filter-quelle"', html)
        self.assertIn(b'id="filter-kategorie"', html)
        self.assertIn(b'name="quelle"', html)
        self.assertIn(b'name="kategorie"', html)
        code, _, js = self.get("/app.js")
        self.assertEqual(code, 200)
        self.assertIn(b'quelle: String(f.get("quelle")', js)
        self.assertIn(b'kategorie: String(f.get("kategorie")', js)
        self.assertIn(b'p.set("quelle", w.quelle)', js)
        self.assertIn(b'p.set("kategorie", w.kategorie)', js)
        self.assertIn(b'"/api/export.csv?" + qs', js)
        self.assertIn(b'"/api/export.json?" + qs', js)


if __name__ == "__main__":
    unittest.main()
