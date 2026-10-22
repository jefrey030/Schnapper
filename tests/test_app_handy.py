"""Tests: Vorlage für eigene Angebote und Startbildschirm-Funktion (Web-App-Manifest)."""
import json
import pathlib
import struct
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import lies_datei  # noqa: E402
from schnapper.web import erstelle_server  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
