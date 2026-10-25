"""Fertigstellungs-Master P2: lokale CSV-/JSON-Downloads ohne Fremdnetz."""
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
from schnapper.web import CSV_FELDER, erstelle_server, exportiere_csv  # noqa: E402


class OfflineDownload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = erstelle_server(ROOT / "app" / "beispiele" / "angebote.csv", port=0)
        cls.base = "http://127.0.0.1:" + str(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.http = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def laden(self, path, method="GET"):
        request = urllib.request.Request(self.base + path, method=method)
        try:
            with self.http.open(request, timeout=5) as r:
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def test_csv_export_hat_download_header_utf8_und_bom(self):
        code, headers, data = self.laden("/api/export.csv?sortierung=preis")
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(headers["Content-Disposition"],
                         'attachment; filename="schnapper-treffer.csv"')
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertTrue(data.startswith(b"\\xef\\xbb\\xbf"))
        self.assertIn(b"\\r\\n", data)
        felder = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
        self.assertTrue(felder)
        self.assertEqual(tuple(felder[0]), CSV_FELDER)

    def test_csv_json_und_suche_enthalten_dieselben_gefilterten_treffer(self):
        qs = "?text=kopfhoerer&sortierung=preis&max_preis=60"
        csvdaten = self.laden("/api/export.csv" + qs)[2].decode("utf-8-sig")
        obj = json.loads(self.laden("/api/export.json" + qs)[2])
        suche = json.loads(self.laden("/api/suche" + qs)[2])
        self.assertEqual(obj, suche)
        ids = [r["id"] for r in csv.DictReader(io.StringIO(csvdaten), delimiter=";")]
        self.assertEqual(ids, [a["id"] for a in suche["treffer"]])
        self.assertEqual([r["gesamtpreis"] for r in csv.DictReader(
            io.StringIO(csvdaten), delimiter=";")],
            [a["gesamtpreis"] for a in suche["treffer"]])

    def test_json_download_header_und_dateiname_fest(self):
        code, headers, raw = self.laden("/api/export.json")
        self.assertEqual(code, 200)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(headers["Content-Disposition"],
                         'attachment; filename="schnapper-treffer.json"')
        self.assertIsInstance(json.loads(raw)["treffer"], list)

    def test_leere_suche_ergibt_korrekte_csv_headerzeile(self):
        code, _, raw = self.laden("/api/export.csv?text=unauffindbarephantasie")
        self.assertEqual(code, 200)
        zeilen = list(csv.reader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(zeilen, [list(CSV_FELDER)])

    def test_ungueltige_filter_blockieren_beide_downloads(self):
        for pfad in ("/api/export.csv", "/api/export.json"):
            for filtertext in ("sortierung=falsch", "min_rabatt=NaN",
                               "max_preis=-1", "zustand=kaputt"):
                with self.subTest(pfad=pfad, filtertext=filtertext):
                    code, _, raw = self.laden(pfad + "?" + filtertext)
                    self.assertEqual(code, 400)
                    self.assertIn("fehler", json.loads(raw))

    def test_head_verhindert_dateiuebertragung(self):
        code, headers, raw = self.laden("/api/export.csv?sortierung=preis", "HEAD")
        self.assertEqual(code, 200)
        self.assertEqual(raw, b"")
        self.assertGreater(int(headers["Content-Length"]), 0)

    def test_mobile_seite_hat_exportlinks(self):
        code, _, raw = self.laden("/")
        self.assertEqual(code, 200)
        html = raw.decode("utf-8")
        self.assertIn('id="export-csv"', html)
        self.assertIn('id="export-json"', html)
        js = self.laden("/app.js")[2].decode("utf-8")
        self.assertIn('function exportLinksAktualisieren()', js)
        self.assertIn('"/api/export.csv?" + qs', js)
        self.assertIn('"/api/export.json?" + qs', js)


class CsvInjectionSchutz(unittest.TestCase):
    def test_formelzellen_werden_zu_text_statt_ausfuehrbar(self):
        beispiele = ["=SUM(1,2)", "+cmd", "-1+2", "@beispiel",
                     "  =HYPERLINK()", "\\t=FORMEL()"]
        for titel in beispiele:
            with self.subTest(titel=titel):
                treffer = {"id": "1", "titel": titel, "gesamtpreis": "10.00",
                           "preis": "10", "versand": "0", "rabatt_prozent": "",
                           "zustand": "gebraucht", "quelle": "eigene",
                           "kategorie": "", "url": "https://shop.example/a",
                           "erfasst_am": "2026-10-25T00:00:00Z", "warnungen": []}
                raw = exportiere_csv({"treffer": [treffer]})
                zeilen = list(csv.DictReader(
                    io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
                self.assertTrue(zeilen[0]["titel"].startswith("'"))
                self.assertNotIn("\\t", zeilen[0]["titel"])

    def test_benutzertext_kann_keine_zusaetzlichen_csv_zeilen_ausloesen(self):
        treffer = {"id": "1", "titel": "Hallo\\r\\n=ANGRIFF()",
                   "quelle": "eigene", "warnungen": ["Achtung\\n=TEST()"]}
        raw = exportiere_csv({"treffer": [treffer]})
        zeilen = list(csv.DictReader(
            io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
        self.assertEqual(len(zeilen), 1)
        self.assertNotIn("\\n", zeilen[0]["titel"])
        self.assertNotIn("\\r", zeilen[0]["titel"])


if __name__ == "__main__":
    unittest.main()
