"""Tests: Vorlage für eigene Angebote und Startbildschirm-Funktion (Web-App-Manifest)."""
import datetime as dt
import json
import pathlib
import struct
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import lies_datei  # noqa: E402
from schnapper.web import erstelle_server  # noqa: E402
from schnapper import openprices as op  # noqa: E402
from schnapper.angebot import AngebotFehler, geld  # noqa: E402

VORLAGE = ROOT / "app" / "vorlagen" / "meine-angebote.csv"
WEB = ROOT / "app" / "schnapper" / "web"


def png_groesse(daten: bytes):
    assert daten[:8] == b"\x89PNG\r\n\x1a\n", "keine PNG-Datei"
    return struct.unpack(">II", daten[16:24])


class Vorlage(unittest.TestCase):
    def test_leere_vorlage_ohne_fehler(self):
        e = lies_datei(VORLAGE)
        self.assertEqual((e.angebote, e.fehler), ([], []))

    def test_ausgefuellte_vorlage_mit_quelle_eigene(self):
        kopf = VORLAGE.read_text(encoding="utf-8").strip()
        zeilen = [kopf,
                  "1;Kopfhörer;49,99;4,90;129,00;gebraucht;eigene;audio;https://shop.example/1;2026-10-22T08:00:00Z",
                  "2;Lampe;10;;;neu;kleinanzeigen;;https://x.example/2;2026-10-22T08:00:00Z"]
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "meine.csv"
            p.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
            e = lies_datei(p)
        self.assertEqual([a.id for a in e.angebote], ["1"])
        self.assertEqual(len(e.fehler), 1)
        self.assertIn("ausgeschlossen", e.fehler[0])

    def test_anleitung_nennt_alle_spalten(self):
        anleitung = (ROOT / "docs" / "EIGENE-ANGEBOTE.md").read_text(encoding="utf-8")
        for spalte in VORLAGE.read_text(encoding="utf-8").strip().split(";"):
            self.assertIn(f"`{spalte}`", anleitung)


class Startbildschirm(unittest.TestCase):
    def test_manifest_inhalt(self):
        m = json.loads((WEB / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual((m["start_url"], m["display"], m["short_name"]), ("/", "standalone", "SCHNAPPER"))
        groessen = {(i["sizes"], i["purpose"]) for i in m["icons"]}
        self.assertTrue({("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= groessen)
        for icon in m["icons"]:
            breite, hoehe = png_groesse((WEB / icon["src"].lstrip("/")).read_bytes())
            self.assertEqual(f"{breite}x{hoehe}", icon["sizes"])

    def test_server_liefert_manifest_und_icons(self):
        server = erstelle_server(VORLAGE, port=0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        basis = f"http://127.0.0.1:{server.server_address[1]}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(basis + "/", timeout=5) as r:
                seite = r.read().decode()
                csp = r.headers["Content-Security-Policy"]
            self.assertIn('rel="manifest" href="/manifest.webmanifest"', seite)
            self.assertIn("manifest-src 'self'", csp)
            for pfad, typ in (("/manifest.webmanifest", "application/manifest+json"),
                              ("/icon-192.png", "image/png"), ("/icon-512.png", "image/png"),
                              ("/icon-maskable-512.png", "image/png")):
                with opener.open(basis + pfad, timeout=5) as r:
                    self.assertTrue(r.headers["Content-Type"].startswith(typ), pfad)
            with opener.open(basis + "/api/suche", timeout=5) as r:
                daten = json.loads(r.read())
            self.assertEqual((daten["eingelesen"], daten["beispieldaten"]), (0, False))
        finally:
            server.shutdown()
            server.server_close()



class Preisvalidierung(unittest.TestCase):
    def test_extrem_grosse_geldbetraege_erzeugen_kontrollierten_fehler(self):
        with self.assertRaises(AngebotFehler):
            geld("1e10000")


class BarcodeWeb(unittest.TestCase):
    """Echter lokaler HTTP-Server, aber niemals ein echter externer Preisabruf."""

    EAN = "4008400402222"

    def setUp(self):
        self.server = erstelle_server(VORLAGE, port=0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.basis = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def post(self, ean, headers=None):
        payload = json.dumps({"ean": ean}).encode("utf-8")
        req = urllib.request.Request(
            self.basis + "/api/openprices", data=payload,
            headers={"X-Schnapper": "1", "Content-Type": "application/json"} if headers is None else headers,
            method="POST",
        )
        try:
            with self.opener.open(req, timeout=5) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_kein_schalter_keine_externe_preisabfrage(self):
        with mock.patch.dict("os.environ", {}, clear=True), mock.patch.object(op, "_abruf") as abruf:
            status, body = self.post(self.EAN)
        self.assertEqual(status, 403)
        self.assertIn("FREIGABE", body["fehler"])
        abruf.assert_not_called()

    def test_schutzheader_und_ungueltiger_barcode(self):
        with mock.patch.dict("os.environ", {op.FREIGABE_VARIABLE: "ja"}, clear=True), \
             mock.patch.object(op, "_abruf") as abruf:
            status_ohne, _ = self.post(self.EAN, headers={"Content-Type": "application/json"})
            status_barcode, _ = self.post("abc")
        self.assertEqual((status_ohne, status_barcode), (403, 400))
        abruf.assert_not_called()

    def test_barcode_zeigt_preis_ohne_eigene_angebote_zu_ersetzen(self):
        heute = dt.date.today().isoformat()
        preis = {
            "id": 77, "product_code": self.EAN, "product_name": "TEST Produkt",
            "price": 1.29, "currency": "EUR", "price_per": "UNIT",
            "date": heute, "location": {"osm_name": "Testladen", "osm_address_city": "Berlin"},
        }
        with mock.patch.dict("os.environ", {op.FREIGABE_VARIABLE: "ja"}, clear=True), \
             mock.patch.object(op, "_abruf", return_value={"items": [preis], "total": 1}) as abruf:
            status, daten = self.post(self.EAN)
        self.assertEqual(status, 200)
        self.assertEqual(daten["treffer"][0]["id"], "openprices-77")
        self.assertIn("ODbL", daten["lizenz"])
        self.assertFalse(daten["beispieldaten"])
        abruf.assert_called_once()
        with self.opener.open(self.basis + "/api/suche", timeout=5) as r:
            eigene = json.loads(r.read())
        self.assertEqual(eigene["eingelesen"], 0)

    def test_zweifach_barcode_abruf_wird_lokal_begrenzt(self):
        self.entered = threading.Event()
        freigabe = threading.Event()
        ergebnis = []

        def langsamer_abruf(_url):
            self.entered.set()
            freigabe.wait(timeout=3)
            return {"items": []}

        with mock.patch.dict("os.environ", {op.FREIGABE_VARIABLE: "ja"}, clear=True), \
             mock.patch.object(op, "_abruf", side_effect=langsamer_abruf) as abruf:
            erster = threading.Thread(target=lambda: ergebnis.append(self.post(self.EAN)))
            erster.start()
            try:
                self.assertTrue(self.entered.wait(timeout=2))
                code, data = self.post(self.EAN)
                self.assertEqual(code, 429)
                self.assertIn("bereits", data["fehler"])
            finally:
                freigabe.set()
                erster.join(timeout=5)
        self.assertEqual(abruf.call_count, 1)
        self.assertEqual(ergebnis[0][0], 200)

    def test_nan_filter_antwortet_400_und_keine_500(self):
        for wert in ("NaN", "Infinity", "-Infinity", "1e999999"):
            with self.assertRaises(urllib.error.HTTPError) as caught:
                self.opener.open(self.basis + "/api/suche?min_rabatt=" + wert, timeout=5)
            self.assertEqual(caught.exception.code, 400)

    def test_browser_hat_barcode_formular(self):
        with self.opener.open(self.basis + "/", timeout=5) as r:
            html = r.read().decode("utf-8")
        self.assertIn('id="barcode-form"', html)
        self.assertIn('id="barcode-status"', html)


if __name__ == "__main__":
    unittest.main()
