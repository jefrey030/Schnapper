"""Fertigstellungsabnahme: CSV-/JSON-Export über echte lokale HTTP-Routen.

Keine externen Netzwerkanfragen, Cloud-Modelle, Quellenzugänge oder Downloads.
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

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import lies_text  # noqa: E402
from schnapper.web import CSV_FELDER, erstelle_server, exportiere_csv  # noqa: E402

HEADER = "id;titel;preis;versand;referenzpreis;zustand;quelle;kategorie;url;erfasst_am"
ZEILEN = [
    "kopf;Kopfhörer Berlin;45;5;90;gebraucht;eigene;Audio;https://shop.example/kopf;2026-10-21T11:00:00Z",
    "rad;TEST Fahrrad;100;0;150;gebraucht;eigene;Rad;https://shop.example/rad;2026-10-21T11:00:00Z",
    "fremd;Kopfhörer fremd;1;0;50;gebraucht;kleinanzeigen;Audio;https://shop.example/fremd;2026-10-21T11:00:00Z",
]


class ExportHttpAbnahme(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        pfad = pathlib.Path(temp.name) / "eigene.csv"
        pfad.write_text(HEADER + "\n" + "\n".join(ZEILEN) + "\n", encoding="utf-8")
        self.server = erstelle_server(pfad, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._schliessen)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _schliessen(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def hole(self, pfad, method="GET"):
        req = urllib.request.Request(self.url + pfad, method=method)
        try:
            with self.opener.open(req, timeout=5) as result:
                return result.status, result.headers, result.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_json_export_ist_identisch_zur_aktuellen_filter_suche(self):
        filtertext = "?text=kopfhoerer&max_preis=50&sortierung=preis"
        status, _, suchtext = self.hole("/api/suche" + filtertext)
        self.assertEqual(status, 200)
        status, kopf, export = self.hole("/api/export.json" + filtertext)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(export), json.loads(suchtext))
        self.assertEqual([t["id"] for t in json.loads(export)["treffer"]], ["kopf"])
        self.assertEqual(json.loads(export)["treffer"][0]["referenzpreis"], "90.00")
        self.assertIn("attachment", kopf["Content-Disposition"])
        self.assertIn("schnapper-treffer.json", kopf["Content-Disposition"])
        self.assertEqual(kopf["X-Content-Type-Options"], "nosniff")
        self.assertEqual(kopf["Cache-Control"], "no-store")

    def test_csv_enthält_nur_gefilterte_und_zulässige_angebote(self):
        status, kopf, body = self.hole("/api/export.csv?sortierung=preis&max_preis=60")
        self.assertEqual(status, 200)
        self.assertEqual(kopf["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("schnapper-treffer.csv", kopf["Content-Disposition"])
        self.assertTrue(body.startswith(b"\xef\xbb\xbf"))
        zeilen = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(zeilen), 1)
        self.assertEqual(zeilen[0]["id"], "kopf")
        self.assertEqual(zeilen[0]["gesamtpreis"], "50.00")
        self.assertEqual(zeilen[0]["referenzpreis"], "90.00")
        self.assertEqual(zeilen[0]["rabatt_prozent"], "44.4")
        self.assertNotIn("fremd", body.decode("utf-8"))

    def test_csv_durch_das_eigene_importformat_wieder_lesbar(self):
        status, _, body = self.hole("/api/export.csv?text=kopfhoerer")
        self.assertEqual(status, 200)
        gelesen = lies_text(body.decode("utf-8-sig"), "csv")
        self.assertEqual(gelesen.fehler, [])
        self.assertEqual(len(gelesen.angebote), 1)
        self.assertEqual(gelesen.angebote[0].referenzpreis, 90)
        self.assertEqual(gelesen.angebote[0].gesamtpreis, 50)

    def test_leeres_suchergebnis_hat_csv_kopfzeile(self):
        status, _, body = self.hole("/api/export.csv?text=unmoeglichername")
        self.assertEqual(status, 200)
        rows = list(csv.reader(io.StringIO(body.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(rows, [list(CSV_FELDER)])
        status, _, body = self.hole("/api/export.json?text=unmoeglichername")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["treffer"], [])

    def test_ungueltige_filter_beim_export_antworten_mit_400_ohne_download(self):
        for endung in ("csv", "json"):
            for q in ("max_preis=0", "min_rabatt=NaN",
                      "sortierung=falsch", "zustand=ausgedacht"):
                with self.subTest(endung=endung, filter=q):
                    status, kopf, body = self.hole(f"/api/export.{endung}?{q}")
                    self.assertEqual(status, 400)
                    self.assertNotIn("Content-Disposition", kopf)
                    self.assertIn("fehler", json.loads(body))

    def test_head_zeigt_download_header_aber_keinen_body(self):
        status, kopf, body = self.hole("/api/export.csv?max_preis=50", "HEAD")
        self.assertEqual(status, 200)
        self.assertIn("attachment", kopf["Content-Disposition"])
        self.assertGreater(int(kopf["Content-Length"]), 10)
        self.assertEqual(body, b"")

    def test_browser_enthaelt_export_links_und_aktive_filter(self):
        status, _, html = self.hole("/")
        self.assertEqual(status, 200)
        self.assertIn(b'id="export-csv"', html)
        self.assertIn(b'id="export-json"', html)
        status, _, js = self.hole("/app.js")
        self.assertEqual(status, 200)
        self.assertIn(b"function exportLinksAktualisieren()", js)
        self.assertIn(b'"/api/export.csv?" + qs', js)
        self.assertIn(b'"/api/export.json?" + qs', js)


class ExportSicherheitsregeln(unittest.TestCase):
    def test_tabellenformeln_und_zeilenkontrolle(self):
        feld = {
            "id": "@gefaehrlich",
            "titel": " \u00a0\u200b=HYPERLINK(\"https://example.invalid\",\"klick\")\r\nzweite Zeile",
            "gesamtpreis": "10.00",
            "preis": "10.00",
            "versand": "0.00",
            "referenzpreis": "50.00",
            "rabatt_prozent": "80.0",
            "quelle": "eigene",
            "kategorie": "\u200b+FORMEL()",
            "url": "https://example.invalid/item",
            "erfasst_am": "2026-10-21T11:00:00Z",
            "warnungen": ["Hinweis\r\nnaechste Zeile"],
        }
        body = exportiere_csv({"treffer": [feld]}).decode("utf-8-sig")
        zeilen = list(csv.DictReader(io.StringIO(body), delimiter=";"))
        self.assertEqual(len(zeilen), 1)
        self.assertTrue(zeilen[0]["id"].startswith("'@"))
        self.assertTrue(zeilen[0]["titel"].startswith("'"))
        self.assertTrue(zeilen[0]["kategorie"].startswith("'"))
        self.assertNotIn("\r", zeilen[0]["titel"])
        self.assertNotIn("\n", zeilen[0]["titel"])
        self.assertEqual(len(body.splitlines()), 2)

    def test_gestaltung_enthaelt_keine_live_preiszusagen(self):
        # Export hat nur bekannte lokale Daten; es existiert keine
        # Open-Prices-Abfrage in den CSV-/JSON-Exportzweigen.
        import inspect
        from schnapper import web
        export = inspect.getsource(web.exportiere_csv)
        self.assertNotIn("openprices", export.lower())
        self.assertNotIn("urllib", export.lower())


if __name__ == "__main__":
    unittest.main()
