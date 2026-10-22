"""Tests für S-010 / F3: Merkliste und Preisalarme als JSON sichern und wiederherstellen."""
import json
import os
import pathlib
import re
import sys
import threading
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.web import SICHERHEIT, erstelle_server  # noqa: E402

BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"
WEB = ROOT / "app" / "schnapper" / "web"
CHROMIUM = pathlib.Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - nur ohne Playwright
    sync_playwright = None

CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def merk(titel="Rad", preis=10.5, url="https://beispiel.example/1"):
    return {"titel": titel, "gesamtpreis": preis, "url": url, "quelle": "beispielmarkt",
            "zustand": "gebraucht", "gemerkt_am": "2026-10-22T10:00:00Z"}


def alarm(text="Rad", max_preis="100", min_rabatt="", zustand=""):
    return {"text": text, "max_preis": max_preis, "min_rabatt": min_rabatt, "zustand": zustand,
            "angelegt_am": "2026-10-22T10:00:00Z"}


def sicherung(merkliste=None, alarme=None, **extra):
    obj = {"format": "schnapper-sicherung", "version": 1, "erstellt_am": "2026-10-22T10:00:00Z",
           "merkliste": {} if merkliste is None else merkliste, "alarme": [] if alarme is None else alarme}
    obj.update(extra)
    return obj


class Statisch(unittest.TestCase):
    """AK9: kein innerHTML, Grenzen unverändert, CSP unverändert, Markup vorhanden."""

    def test_ak9_app_js(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        code = "\n".join(re.sub(r"//.*$", "", z) for z in js.splitlines())
        self.assertNotIn("innerHTML", code)
        self.assertIn("const MAX_MERK = 200;", js)
        self.assertIn("const MAX_ALARME = 50;", js)
        self.assertIn("const SICHERUNG_VERSION = 1;", js)
        self.assertIn("const MAX_SICHERUNG = 1024 * 1024;", js)
        self.assertIn('$("sicherung-export").addEventListener("click", sicherungErstellen)', js)
        self.assertIn('$("sicherung-datei").addEventListener("change", sicherungLaden)', js)
        start = js.index("async function sicherungLaden")
        funktion = js[start:js.index("\n}\n", start)]
        self.assertNotIn("fetch(", funktion)

    def test_ak9_csp_unveraendert(self):
        self.assertEqual(SICHERHEIT["Content-Security-Policy"], CSP)

    def test_markup(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        for teil in ('id="sicherung"', 'id="sicherung-export"', 'id="sicherung-datei" type="file" accept=".json,application/json"',
                     'id="sicherung-status" class="status" aria-live="polite"', 'id="sicherung-fehler"',
                     'id="datei" type="file" accept=".csv,.json,text/csv,application/json"'):
            self.assertIn(teil, html)


@unittest.skipUnless(sync_playwright is not None and (CHROMIUM.is_file() or os.environ.get("PLAYWRIGHT_BROWSERS_PATH")),
                     "Playwright oder Chromium fehlt")
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        kw = {"executable_path": str(CHROMIUM)} if CHROMIUM.is_file() else {}
        cls.browser = cls.pw.chromium.launch(**kw)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()

    def setUp(self):
        self.server = erstelle_server(BEISPIEL, port=0)
        self.basis = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.meldungen, self.fremd = [], []
        self.kontext = self.browser.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True)
        # AK8: nur der lokale Server; alles andere wird blockiert und protokolliert.
        self.kontext.route(re.compile(r"^(?!" + re.escape(self.basis) + "|blob:).*"), lambda r: r.abort())
        self.seite = self.kontext.new_page()
        self.seite.on("request", lambda r: None if r.url.startswith((self.basis + "/", "blob:")) else self.fremd.append(r.url))
        self.seite.on("console", lambda m: self.meldungen.append(m.text) if m.type == "error" else None)
        self.seite.on("pageerror", lambda e: self.meldungen.append(str(e)))
        self.seite.goto(self.basis + "/")
        self.seite.wait_for_selector("#treffer li")

    def tearDown(self):
        self.kontext.close()
        self.server.shutdown()
        self.server.server_close()
        self.assertEqual(self.fremd, [])
        self.assertEqual(self.meldungen, [])

    # ---------- Hilfen ----------
    def warte(self, ausdruck, sekunden=10):
        """Wie wait_for_function, aber ohne eval im Seitenkontext (die CSP verbietet 'unsafe-eval')."""
        ende = time.monotonic() + sekunden
        while not self.seite.evaluate(ausdruck):
            if time.monotonic() > ende:
                self.fail("Zeitüberschreitung: " + ausdruck)
            time.sleep(0.05)

    def roh(self):
        return self.seite.evaluate("[localStorage.getItem('schnapper.merkliste'), localStorage.getItem('schnapper.alarme')]")

    def stand(self):
        m, a = self.roh()
        return (json.loads(m) if m else None, json.loads(a) if a else None)

    def lade(self, inhalt, name="sicherung.json"):
        self.seite.evaluate("document.getElementById('sicherung-status').textContent = ''")
        daten = inhalt if isinstance(inhalt, bytes) else json.dumps(inhalt).encode("utf-8")
        self.seite.set_input_files("#sicherung-datei", {"name": name, "mimeType": "application/json", "buffer": daten})
        self.warte("document.getElementById('sicherung-status').textContent.length > 0")
        return self.seite.locator("#sicherung-status").text_content()

    def fehlerliste(self):
        return self.seite.locator("#sicherung-fehler li").all_text_contents()

    def stand_anlegen(self):
        """Zwei Angebote merken, einen Preisalarm anlegen."""
        knoepfe = self.seite.locator("#treffer .merken")
        knoepfe.nth(0).click()
        knoepfe.nth(1).click()
        self.warte("Object.keys(JSON.parse(localStorage.getItem('schnapper.merkliste')||'{}')).length === 2")
        self.seite.fill("#text", "Kopfhörer")
        self.seite.fill('[name="max_preis"]', "80")
        self.warte("!document.getElementById('alarm-anlegen').disabled")
        self.seite.click("#alarm-anlegen")
        self.warte("JSON.parse(localStorage.getItem('schnapper.alarme')||'[]').length === 1")

    # ---------- Tests ----------
    def test_ak1_ak2_export_und_rundreise(self):
        self.stand_anlegen()
        vorher = self.stand()
        self.assertEqual(len(vorher[0]), 2)
        self.seite.click('[data-ansicht="alarme"]')
        with self.seite.expect_download() as info:
            self.seite.click("#sicherung-export")
        download = info.value
        self.assertRegex(download.suggested_filename, r"^schnapper-sicherung-\d{4}-\d{2}-\d{2}\.json$")
        inhalt = pathlib.Path(download.path()).read_bytes()
        obj = json.loads(inhalt)
        self.assertEqual((obj["format"], obj["version"]), ("schnapper-sicherung", 1))
        self.assertEqual((obj["merkliste"], obj["alarme"]), vorher)
        self.assertIn("erstellt_am", obj)

        self.seite.evaluate("localStorage.clear()")
        self.seite.reload()
        self.seite.wait_for_selector("#treffer li")
        self.assertEqual(self.roh(), [None, None])
        self.assertTrue(self.seite.locator("#anzahl-merk").is_hidden())

        self.seite.click('[data-ansicht="alarme"]')
        meldung = self.lade(inhalt, download.suggested_filename)
        self.assertIn("Wiederhergestellt: 2 gemerkt, 1 Alarme; 0 ungültige Einträge übersprungen", meldung)
        self.assertEqual(self.stand(), vorher)
        self.assertEqual(self.seite.locator("#anzahl-merk").text_content(), "2")
        self.seite.wait_for_selector("#alarm-liste li")
        self.assertEqual(self.seite.locator("#alarm-liste > li").count(), 1)
        self.assertIn("Kopfhörer", self.seite.locator("#alarm-liste .titel").text_content())
        self.seite.click('[data-ansicht="merkliste"]')
        self.seite.wait_for_selector("#merk-liste li")
        self.assertEqual(self.seite.locator("#merk-liste > li").count(), 2)
        self.assertLessEqual(self.seite.evaluate("document.documentElement.scrollWidth"), 390)

    def test_ak3_ak4_ak5_abweisungen_aendern_nichts(self):
        self.stand_anlegen()
        self.seite.click('[data-ansicht="alarme"]')
        vorher = self.roh()
        viele_merk = {f"id{i}": merk(f"Rad {i}") for i in range(201)}
        viele_alarme = [alarm(f"Rad {i}") for i in range(51)]
        faelle = [
            ("kaputt", b"{kein json", "kein gültiges JSON"),
            ("version 2", sicherung(version=2), "Version 2"),
            ("format", sicherung(format="etwas-anderes"), "format"),
            ("zu gross", b'{"x":"' + b"a" * (1024 * 1024) + b'"}', "1 MiB"),
            ("201 merk", sicherung(viele_merk), "max. 200"),
            ("51 alarme", sicherung(alarme=viele_alarme), "max. 50"),
            ("merkliste als liste", sicherung(merkliste=[]), "Merkliste"),
        ]
        for name, inhalt, hinweis in faelle:
            with self.subTest(name):
                meldung = self.lade(inhalt)
                self.assertIn("abgewiesen", meldung)
                self.assertIn(hinweis, meldung)
                self.assertIn("Nichts geändert", meldung)
                self.assertEqual(self.roh(), vorher)

    def test_ak6_ak7_gemischt_und_xss(self):
        self.seite.click('[data-ansicht="alarme"]')
        boese = '<img src=x onerror="window.__xss=1">'
        datei = sicherung(
            merkliste={
                "gut": {**merk(boese), "geheim": "weg"},
                "preis-x": merk(preis="x"),
                "preis-neg": merk(preis=-1),
                "preis-text": merk(preis="54.89"),
                "js-url": merk(url="javascript:alert(1)"),
                "": merk(),
                "ohne-titel": merk(titel=""),
            },
            alarme=[
                {**alarm("Rad"), "extra": 1},
                alarm("Rad"),  # Dublette
                alarm("Bohrer", max_preis="", min_rabatt=""),
                alarm("Säge", max_preis="10€"),
                alarm("Tisch", zustand="kaputt"),
                alarm("Lampe", max_preis="", min_rabatt="20,5", zustand="neu"),
            ])
        meldung = self.lade(datei)
        self.assertIn("Wiederhergestellt: 2 gemerkt, 2 Alarme; 9 ungültige Einträge übersprungen", meldung)
        fehler = self.fehlerliste()
        self.assertEqual(len(fehler), 9)
        for teil in ("„preis-x“ ungültig (gesamtpreis)", "„preis-neg“ ungültig (gesamtpreis)", "„js-url“ ungültig (url)", "„“ ungültig (Schlüssel)",
                     "„ohne-titel“ ungültig (titel)", "Eintrag 2 doppelt", "Eintrag 3 ungültig (max_preis/min_rabatt)",
                     "Eintrag 4 ungültig (max_preis)", "Eintrag 5 ungültig (zustand)"):
            self.assertTrue(any(teil in f for f in fehler), teil)
        m, a = self.stand()
        self.assertEqual(sorted(m), ["gut", "preis-text"])
        self.assertEqual(m["preis-text"]["gesamtpreis"], "54.89")
        self.assertEqual(set(m["gut"]), {"titel", "gesamtpreis", "url", "quelle", "zustand", "gemerkt_am"})
        self.assertEqual(m["gut"]["titel"], boese)
        self.assertEqual([x["text"] for x in a], ["Rad", "Lampe"])
        self.assertNotIn("extra", a[0])
        # AK7: Titel nur als Text, kein <img> im DOM
        self.seite.click('[data-ansicht="merkliste"]')
        self.seite.wait_for_selector("#merk-liste li")
        self.assertIn(boese, self.seite.locator("#merk-liste .titel").all_text_contents())
        self.assertEqual(self.seite.locator("img").count(), 0)
        self.assertIsNone(self.seite.evaluate("window.__xss"))
        self.assertEqual(self.seite.locator("#merk-liste .link").count(), 2)


if __name__ == "__main__":
    unittest.main()
