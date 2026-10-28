"""Tests für S-009 / F2: Angebot direkt in der App erfassen und als CSV herunterladen."""
import json
import os
import pathlib
import re
import sys
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import lies_text  # noqa: E402
from schnapper.verlauf import Verlauf, normalisiere_url  # noqa: E402
from schnapper.web import MAX_ANGEBOT, erstelle_server  # noqa: E402

BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"
VORLAGE = ROOT / "app" / "vorlagen" / "meine-angebote.csv"


def _finde_chromium(basis=None):
    """Sucht das installierte Chromium (höchste Versionsnummer) statt eines fest verdrahteten Pfads."""
    if basis is None:
        basis = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or "/opt/pw-browsers"
    beste, beste_nr = None, -1
    for kandidat in pathlib.Path(basis).glob("chromium-*/chrome-linux*/chrome"):
        nummer = kandidat.parent.parent.name[len("chromium-"):]
        if not nummer.isdigit() or not kandidat.is_file():
            continue
        if int(nummer) > beste_nr:
            beste, beste_nr = kandidat, int(nummer)
    return beste


CHROMIUM = _finde_chromium()

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - nur ohne Playwright
    sync_playwright = None

GUELTIG = {"titel": "Lastenrad Testmodell", "preis": "450,00", "versand": "19.90", "referenzpreis": "900",
           "zustand": "gebraucht", "url": "https://kleinanzeigen.example/rad/1", "kategorie": "Fahrrad"}


class ServerTest(unittest.TestCase):
    """Jeder Test bekommt einen frischen Server mit der Beispielliste (nur 127.0.0.1)."""

    def setUp(self):
        self.server = erstelle_server(BEISPIEL, port=0)
        self.basis = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def hole(self, pfad, daten=None, kopf=None):
        req = urllib.request.Request(self.basis + pfad, data=daten, headers=kopf or {},
                                     method="POST" if daten is not None else "GET")
        try:
            with self.opener.open(req, timeout=5) as r:
                return r.status, r.headers, r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def erfasse(self, daten, kopf=None):
        roh = daten if isinstance(daten, bytes) else json.dumps(daten).encode("utf-8")
        k = {"X-Schnapper": "1", "Content-Type": "application/json"} if kopf is None else kopf
        status, _, inhalt = self.hole("/api/angebot", roh, k)
        return status, json.loads(inhalt)

    def suche(self, query=""):
        return json.loads(self.hole("/api/suche?" + query)[2])


class AngebotErfassen(ServerTest):
    def test_lokal(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_ak1_erfassen_und_finden(self):
        status, antwort = self.erfasse(GUELTIG)
        self.assertEqual(status, 201)
        self.assertTrue(antwort["id"].startswith("e-"))
        self.assertEqual(antwort["anzahl"], 1)
        daten = self.suche("text=Lastenrad")
        self.assertEqual(len(daten["treffer"]), 1)
        t = daten["treffer"][0]
        self.assertEqual((t["id"], t["quelle"], t["preis"], t["versand"]), (antwort["id"], "eigene", "450.00", "19.90"))

    def test_ak2_ohne_header_403(self):
        status, _ = self.erfasse(GUELTIG, kopf={"Content-Type": "application/json"})
        self.assertEqual(status, 403)
        self.assertTrue(self.suche()["beispieldaten"])

    def test_ak2_zu_gross_413(self):
        status, _ = self.erfasse({**GUELTIG, "kategorie": "x" * (MAX_ANGEBOT + 1)})
        self.assertEqual(status, 413)

    def test_ak2_kaputtes_json_400(self):
        for roh in (b"{kaputt", b"[1, 2]", "\"text\"".encode()):
            with self.subTest(roh):
                self.assertEqual(self.erfasse(roh)[0], 400)

    def test_ak3_ungueltig_422_liste_unveraendert(self):
        vorher = self.suche()
        for aenderung in ({"preis": "0"}, {"preis": "abc"}, {"url": "http://kleinanzeigen.example/rad/1"},
                          {"zustand": "super"}, {"titel": ""}):
            with self.subTest(aenderung):
                status, antwort = self.erfasse({**GUELTIG, **aenderung})
                self.assertEqual(status, 422)
                self.assertIn("fehler", antwort)
                self.assertEqual(self.suche(), vorher)

    def test_ak4_clientfelder_ignoriert(self):
        status, antwort = self.erfasse({**GUELTIG, "quelle": "ebay", "id": "gefaelscht",
                                        "erfasst_am": "2000-01-01T00:00:00Z", "waehrung": "USD"})
        self.assertEqual(status, 201)
        self.assertNotEqual(antwort["id"], "gefaelscht")
        t = self.suche("text=Lastenrad")["treffer"][0]
        self.assertEqual(t["quelle"], "eigene")
        self.assertEqual(t["id"], antwort["id"])
        self.assertFalse(t["erfasst_am"].startswith("2000"))

    def test_ak5_beispielliste_wird_ersetzt(self):
        self.assertTrue(self.suche()["beispieldaten"])
        _, a = self.erfasse(GUELTIG)
        daten = self.suche()
        self.assertFalse(daten["beispieldaten"])
        self.assertEqual(daten["eingelesen"], 1)
        self.assertEqual([t["id"] for t in daten["treffer"]], [a["id"]])
        _, b = self.erfasse({**GUELTIG, "titel": "Zweites Rad", "url": "https://kleinanzeigen.example/rad/2"})
        self.assertEqual(b["anzahl"], 2)
        self.assertEqual({t["id"] for t in self.suche()["treffer"]}, {a["id"], b["id"]})


class CsvExport(ServerTest):
    def test_ak6_kopfzeile_wie_vorlage(self):
        status, kopf, inhalt = self.hole("/api/angebote.csv")
        self.assertEqual(status, 200)
        self.assertEqual(kopf["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn('filename="meine-angebote.csv"', kopf["Content-Disposition"])
        self.assertEqual(kopf["X-Content-Type-Options"], "nosniff")
        vorlage_kopf = VORLAGE.read_text(encoding="utf-8-sig").splitlines()[0]
        self.assertEqual(inhalt.decode("utf-8").splitlines(), [vorlage_kopf])  # Beispielliste: nur Kopfzeile

    def test_ak6_roundtrip(self):
        _, a = self.erfasse({**GUELTIG, "titel": "Sofa; mit \"Kissen\""})
        _, b = self.erfasse({**GUELTIG, "titel": "Lampe", "referenzpreis": "", "kategorie": "",
                             "url": "https://kleinanzeigen.example/lampe/2"})
        text = self.hole("/api/angebote.csv")[2].decode("utf-8")
        self.assertEqual(text.splitlines()[0], VORLAGE.read_text(encoding="utf-8-sig").splitlines()[0])
        zurueck = lies_text(text, "csv")
        self.assertEqual(zurueck.fehler, [])
        self.assertEqual([x.id for x in zurueck.angebote], [a["id"], b["id"]])
        sofa, lampe = zurueck.angebote
        self.assertEqual(sofa.titel, "Sofa; mit \"Kissen\"")
        self.assertEqual(str(sofa.preis), "450.00")
        self.assertEqual(sofa.quelle, "eigene")
        self.assertIsNone(lampe.referenzpreis)
        treffer = {t["id"]: t for t in self.suche()["treffer"]}
        self.assertEqual(sofa.erfasst_am.isoformat(), treffer[a["id"]]["erfasst_am"])


class Oberflaeche(ServerTest):
    def test_ak7_formular_und_js(self):
        html = self.hole("/")[2].decode("utf-8")
        for teil in ('id="erfassen"', 'id="angebot-form"', 'name="titel"', 'maxlength="300"', 'name="preis"',
                     'name="versand"', 'name="referenzpreis"', 'name="zustand"', 'name="url"', 'type="url"',
                     'name="kategorie"', 'id="angebot-status"', 'id="csv-download"', 'href="/api/angebote.csv"',
                     "Quelle: eigene", "Angebot hinzufügen"):
            self.assertIn(teil, html)
        self.assertNotIn('name="quelle"', html)
        js = self.hole("/app.js")[2].decode("utf-8")
        start = js.index("async function angebotSpeichern")
        funktion = js[start:js.index("\n}\n", start)]
        self.assertIn("/api/angebot", funktion)
        self.assertIn("X-Schnapper", funktion)
        self.assertNotIn("innerHTML", funktion)
        # Im gesamten Code nur als Kommentar erwähnt (Zeile 2: „nie innerHTML“), nie verwendet.
        code = "\n".join(re.sub(r"//.*$", "", z) for z in js.splitlines())
        self.assertNotIn("innerHTML", code)
        self.assertIn('$("angebot-form").addEventListener("submit", angebotSpeichern)', js)

    def test_chromium_suche_leer(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(_finde_chromium(tmp))

    def test_chromium_suche_hoechste_nummer(self):
        with tempfile.TemporaryDirectory() as tmp:
            for teil in ("chromium-999/chrome-linux", "chromium-1243/chrome-linux64",
                         "chromium_headless_shell-2000/chrome-linux"):
                ordner = pathlib.Path(tmp, teil)
                ordner.mkdir(parents=True)
                (ordner / "chrome").write_text("", encoding="utf-8")
            self.assertEqual(_finde_chromium(tmp), pathlib.Path(tmp, "chromium-1243", "chrome-linux64", "chrome"))


class ErfassenAtomar(ServerTest):
    """Nach dem Merge von main (#37, #42): Erfassen folgt dem atomaren Import-/Verlaufsmodell."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.verlauf_pfad = pathlib.Path(self._tmp.name, "verlauf.json")
        self.verlaeufe = []
        original = Verlauf.laden.__func__

        def fang(cls, pfad):
            v = original(cls, pfad)
            self.verlaeufe.append(v)
            return v

        with mock.patch.object(Verlauf, "laden", classmethod(fang)):
            self.server = erstelle_server(BEISPIEL, port=0, verlauf=self.verlauf_pfad)
        self.verlauf = self.verlaeufe[0]
        self.basis = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def tearDown(self):
        super().tearDown()
        self._tmp.cleanup()

    def test_speicherfehler_500_liste_und_verlauf_unveraendert(self):
        vorher = self.suche()
        datei_vorher = self.verlauf_pfad.read_bytes()
        schluessel = normalisiere_url(GUELTIG["url"])
        self.assertNotIn(schluessel, self.verlauf._daten)
        with mock.patch.object(Verlauf, "speichern", side_effect=OSError("Datenträger voll")):
            status, antwort = self.erfasse(GUELTIG)
        self.assertEqual(status, 500)
        self.assertTrue(antwort["fehler"].startswith("Angebot nicht übernommen"))
        self.assertEqual(self.suche(), vorher)
        self.assertTrue(self.suche()["beispieldaten"])
        self.assertNotIn(schluessel, self.verlauf._daten)  # Rollback im RAM
        self.assertEqual(self.verlauf_pfad.read_bytes(), datei_vorher)
        # Danach klappt derselbe Vorgang wieder – und landet dann auch im Verlauf.
        status, antwort = self.erfasse(GUELTIG)
        self.assertEqual((status, antwort["anzahl"]), (201, 1))
        self.assertEqual(len(self.verlauf._daten[schluessel]), 1)
        self.assertIn(schluessel, self.verlauf_pfad.read_text(encoding="utf-8"))

    def test_mehrdeutiger_preis_422_liste_unveraendert(self):
        vorher = self.suche()
        datei_vorher = self.verlauf_pfad.read_bytes()
        status, antwort = self.erfasse({**GUELTIG, "preis": "1,234"})
        self.assertEqual(status, 422)
        self.assertIn("fehler", antwort)
        self.assertEqual(self.suche(), vorher)
        self.assertEqual(self.verlauf_pfad.read_bytes(), datei_vorher)

    def test_url_mit_zugangsdaten_422(self):
        vorher = self.suche()
        status, antwort = self.erfasse({**GUELTIG, "url": "https://nutzer:pw@shop.example/x"})
        self.assertEqual(status, 422)
        self.assertIn("fehler", antwort)
        self.assertEqual(self.suche(), vorher)


@unittest.skipUnless(sync_playwright is not None and (CHROMIUM is not None or os.environ.get("PLAYWRIGHT_BROWSERS_PATH")),
                     "Playwright oder Chromium fehlt")
class Browser(ServerTest):
    def test_ak8_erfassen_und_csv_im_browser(self):
        meldungen = []
        with sync_playwright() as p:
            kw = {"executable_path": str(CHROMIUM)} if CHROMIUM else {}
            browser = p.chromium.launch(**kw)
            try:
                kontext = browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
                # Nur der lokale Server; alles andere wird blockiert.
                kontext.route(re.compile(r"^(?!" + re.escape(self.basis) + ").*"), lambda r: r.abort())
                seite = kontext.new_page()
                seite.on("console", lambda m: meldungen.append(m.text) if m.type == "error" else None)
                seite.on("pageerror", lambda e: meldungen.append(str(e)))
                seite.goto(self.basis + "/")
                seite.wait_for_selector("#treffer li")
                form = seite.locator("#angebot-form")
                form.locator('[name="titel"]').fill("Browser Lastenrad")
                form.locator('[name="preis"]').fill("450,00")
                form.locator('[name="versand"]').fill("19,90")
                form.locator('[name="referenzpreis"]').fill("900")
                form.locator('[name="zustand"]').select_option("gebraucht")
                form.locator('[name="url"]').fill("https://kleinanzeigen.example/rad/1")
                form.locator('[name="kategorie"]').fill("Fahrrad")
                form.locator('button[type="submit"]').click()
                seite.wait_for_selector("#treffer >> text=Browser Lastenrad")
                self.assertIn("Gespeichert", seite.locator("#angebot-status").text_content())
                self.assertEqual(seite.locator("#treffer > li").count(), 1)  # Beispieldaten verworfen
                breite = seite.evaluate("document.documentElement.scrollWidth")
                self.assertLessEqual(breite, 390)
                with seite.expect_download() as info:
                    seite.locator("#csv-download").click()
                download = info.value
                self.assertEqual(download.suggested_filename, "meine-angebote.csv")
                inhalt = pathlib.Path(download.path()).read_text(encoding="utf-8")
                self.assertIn("Browser Lastenrad", inhalt)
                self.assertIn(";eigene;", inhalt)
            finally:
                browser.close()
        self.assertEqual(meldungen, [])


class ErfassenTypen(ServerTest):
    """Lauf 20261028-1829: Typ- und Längenprüfung der Erfassungsfelder in POST /api/angebot."""

    def pruefe_422(self, aenderung, feld):
        vorher = self.suche()
        status, antwort = self.erfasse({**GUELTIG, **aenderung})
        self.assertEqual(status, 422, antwort)
        self.assertIn(feld, antwort["fehler"])
        self.assertEqual(self.suche(), vorher)

    def test_textfelder_nur_text(self):
        faelle = [("titel", {"a": 1}), ("titel", ["x"]), ("titel", True), ("titel", 5), ("titel", None),
                  ("url", None), ("url", ["https://kleinanzeigen.example/rad/1"]),
                  ("zustand", {"z": "neu"}), ("kategorie", {"k": 1}), ("kategorie", False), ("kategorie", 7)]
        for feld, wert in faelle:
            with self.subTest(feld=feld, wert=wert):
                self.pruefe_422({feld: wert}, feld)

    def test_geldfelder_nur_text_oder_zahl(self):
        faelle = [("preis", True), ("preis", [450]), ("preis", {"p": 1}), ("preis", None),
                  ("versand", False), ("versand", []), ("referenzpreis", {"r": 900}), ("referenzpreis", True)]
        for feld, wert in faelle:
            with self.subTest(feld=feld, wert=wert):
                self.pruefe_422({feld: wert}, feld)

    def test_zahlen_und_leere_optionale_felder_gueltig(self):
        for aenderung in ({"preis": 450}, {"preis": 19.9, "versand": 0, "referenzpreis": 900},
                          {"kategorie": None, "zustand": None, "versand": None, "referenzpreis": None}):
            with self.subTest(aenderung):
                status, antwort = self.erfasse({**GUELTIG, **aenderung})
                self.assertEqual(status, 201, antwort)

    def test_kategorie_laenge(self):
        from schnapper.web import MAX_KATEGORIE
        self.assertEqual(MAX_KATEGORIE, 100)
        html = (ROOT / "app" / "schnapper" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertRegex(html, rf'name="kategorie"[^>]*maxlength="{MAX_KATEGORIE}"')
        self.pruefe_422({"kategorie": "k" * 101}, "kategorie")
        status, antwort = self.erfasse({**GUELTIG, "kategorie": "  " + "k" * 100 + "  "})
        self.assertEqual(status, 201, antwort)
        self.assertEqual(self.suche("text=Lastenrad")["treffer"][0]["kategorie"], "k" * 100)


if __name__ == "__main__":
    unittest.main()
