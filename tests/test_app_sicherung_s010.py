"""Tests für S-010 / F3: Merkliste und Preisalarme als JSON sichern und wiederherstellen."""
import json
import os
import pathlib
import re
import sys
import tempfile
import threading
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.web import SICHERHEIT, erstelle_server  # noqa: E402

BEISPIEL = ROOT / "app" / "beispiele" / "angebote.csv"
WEB = ROOT / "app" / "schnapper" / "web"


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

    def test_alarm_anlegen_nutzt_gemeinsame_pruefung(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertEqual(js.count("function alarmFehler("), 1)
        start = js.index("async function alarmAnlegen")
        funktion = js[start:js.index("\n}\n", start)]
        self.assertIn("alarmFehler(", funktion)
        self.assertLess(funktion.index("alarmFehler("), funktion.index("fetch("))
        start = js.index("function sicherungPruefen")
        self.assertIn("alarmFehler(w)", js[start:js.index("\n}\n", start)])

    def test_alarmpruefung_wie_server(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        self.assertFalse("zahlText" in js, "alte Prüfung zahlText noch vorhanden")
        self.assertIn("/^[0-9]{1,9}(?:[.,][0-9]{1,2})?$/.test(x) && zahlWert(x) > 0", js)
        self.assertIn("/^[0-9]{1,3}(?:[.,][0-9]{1,2})?$/.test(x) && zahlWert(x) >= 0 && zahlWert(x) <= 100", js)

    def test_ak9_csp_unveraendert(self):
        self.assertEqual(SICHERHEIT["Content-Security-Policy"], CSP)

    def test_markup(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        for teil in ('id="sicherung"', 'id="sicherung-export"', 'id="sicherung-datei" type="file" accept=".json,application/json"',
                     'id="sicherung-status" class="status" aria-live="polite"', 'id="sicherung-fehler"',
                     'id="datei" type="file" accept=".csv,.json,text/csv,application/json"'):
            self.assertIn(teil, html)

    def test_chromium_suche_leer(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(_finde_chromium(pathlib.Path(tmp)))

    def test_chromium_suche_hoechste_nummer(self):
        with tempfile.TemporaryDirectory() as tmp:
            basis = pathlib.Path(tmp)
            for teil in ("chromium-999/chrome-linux/chrome", "chromium-1243/chrome-linux64/chrome",
                         "chromium_headless_shell-2000/chrome-linux/chrome"):
                datei = basis / teil
                datei.parent.mkdir(parents=True)
                datei.write_text("", encoding="utf-8")
            self.assertEqual(_finde_chromium(basis), basis / "chromium-1243/chrome-linux64/chrome")


@unittest.skipUnless(sync_playwright is not None and (CHROMIUM is not None or os.environ.get("PLAYWRIGHT_BROWSERS_PATH")),
                     "Playwright oder Chromium fehlt")
class Browser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        kw = {"executable_path": str(CHROMIUM)} if CHROMIUM else {}
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

    def test_proto_schluessel_wird_gemeldet(self):
        """Ein Merkeintrag mit Schlüssel "__proto__" wird gemeldet statt still verworfen (F3: ungültige melden)."""
        self.seite.click('[data-ansicht="alarme"]')
        daten = json.dumps(sicherung(merkliste={"__proto__": merk("Böse"), "gut": merk("Rad")})).encode("utf-8")
        self.assertIn(b'"__proto__"', daten)
        meldung = self.lade(daten)
        self.assertIn("Wiederhergestellt: 1 gemerkt, 0 Alarme; 1 ungültige Einträge übersprungen", meldung)
        fehler = self.fehlerliste()
        self.assertEqual(len(fehler), 1)
        self.assertIn("„__proto__“ ungültig (Schlüssel)", fehler[0])
        self.assertEqual(sorted(self.stand()[0]), ["gut"])
        self.assertTrue(self.seite.evaluate(
            "Object.getPrototypeOf(JSON.parse(localStorage.getItem('schnapper.merkliste'))) === Object.prototype"))
        self.assertIsNone(self.seite.evaluate("({}).titel"))

    # ---------- Speicherfehler bei der Wiederherstellung (Befund 28.10.2026) ----------
    def _speicherfehler(self, art):
        """Lässt localStorage gezielt fehlschlagen: 'merkliste'/'alarme' = setItem dieses Schlüssels, 'lesen' = getItem."""
        self.seite.evaluate("""(art) => {
          const setOrig = Storage.prototype.setItem, getOrig = Storage.prototype.getItem;
          window.__speicherfehlerAus = () => { Storage.prototype.setItem = setOrig; Storage.prototype.getItem = getOrig; };
          if (art === 'lesen') {
            Storage.prototype.getItem = function () { throw new DOMException('gesperrt', 'SecurityError'); };
          } else {
            Storage.prototype.setItem = function (k, v) {
              if (k === 'schnapper.' + art) throw new DOMException('voll', 'QuotaExceededError');
              return setOrig.call(this, k, v);
            };
          }
        }""", art)

    def _speicherfehler_pruefen(self, art):
        self.stand_anlegen()
        vorher_roh = self.roh()
        self.seite.click('[data-ansicht="alarme"]')
        self._speicherfehler(art)
        meldung = self.lade(sicherung(merkliste={"neu": merk("Neu")}, alarme=[alarm("Neu")]))
        self.assertIn("Wiederherstellung fehlgeschlagen", meldung)
        self.assertIn("Nichts geändert", meldung)
        self.assertNotIn("Wiederhergestellt", meldung)
        self.seite.evaluate("window.__speicherfehlerAus()")
        self.assertEqual(self.roh(), vorher_roh)
        # Anzeige zeigt weiter den alten Stand, auch nach Neuladen.
        self.assertEqual(self.seite.locator("#anzahl-merk").text_content(), "2")
        self.seite.reload()
        self.seite.wait_for_selector("#treffer li")
        self.assertEqual(self.roh(), vorher_roh)
        self.assertEqual(self.seite.locator("#anzahl-merk").text_content(), "2")

    def test_speicherfehler_erster_schreibvorgang(self):
        self._speicherfehler_pruefen("merkliste")

    def test_speicherfehler_zweiter_schreibvorgang_rollback(self):
        self._speicherfehler_pruefen("alarme")

    def test_speicherfehler_vor_dem_schreiben(self):
        self._speicherfehler_pruefen("lesen")

    def test_alarmgrenzen_wie_server(self):
        """Nur Alarme übernehmen, die /api/suche auch akzeptiert (max_preis > 0, 2 Nachkommastellen, Rabatt 0–100)."""
        self.seite.click('[data-ansicht="alarme"]')
        datei = sicherung(alarme=[
            alarm("Rad", max_preis="12,50"),
            alarm("Säge", max_preis="0"),
            alarm("Tisch", max_preis="1,234"),
            alarm("Lampe", max_preis="", min_rabatt="150"),
            alarm("Bohrer", max_preis="", min_rabatt="100"),
        ])
        meldung = self.lade(datei)
        self.assertIn("Wiederhergestellt: 0 gemerkt, 2 Alarme; 3 ungültige Einträge übersprungen", meldung)
        fehler = self.fehlerliste()
        self.assertEqual(len(fehler), 3)
        for teil in ("Eintrag 2 ungültig (max_preis)", "Eintrag 3 ungültig (max_preis)", "Eintrag 4 ungültig (min_rabatt)"):
            self.assertTrue(any(teil in f for f in fehler), teil)
        _, a = self.stand()
        self.assertEqual([x["text"] for x in a], ["Rad", "Bohrer"])
        # Jeder übernommene Alarm wird vom Server akzeptiert: keine Karte zeigt „Eingabe ungültig“.
        self.warte("document.querySelectorAll('#alarm-liste > li').length === 2 && "
                   "[...document.querySelectorAll('#alarm-liste .ausgeloest')].every((e) => e.textContent.length > 0)")
        marken = self.seite.locator("#alarm-liste .ausgeloest").all_text_contents()
        self.assertEqual(len(marken), 2)
        self.assertFalse(any("Eingabe ungültig" in m for m in marken), marken)

        # Grenzfälle direkt an der reinen Prüffunktion (AK4/AK5).
        def pruefe(feld, wert):
            w = alarm("X", max_preis="", min_rabatt="")
            w[feld] = wert
            if feld == "min_rabatt" and wert == "":
                w["max_preis"] = "5"
            return self.seite.evaluate("(o) => sicherungPruefen(o)", sicherung(alarme=[w]))

        for feld, wert in (("max_preis", "0"), ("max_preis", "0,00"), ("max_preis", "1,234"), ("max_preis", "1.2345"),
                           ("max_preis", "10€"), ("max_preis", "-5"), ("min_rabatt", "150"), ("min_rabatt", "100,5")):
            with self.subTest(abgewiesen=(feld, wert)):
                r = pruefe(feld, wert)
                self.assertEqual(r["alarme"], [])
                self.assertEqual(r["fehler"], [f"Alarme: Eintrag 1 ungültig ({feld})"])
        for feld, wert in (("max_preis", "100"), ("max_preis", "12,50"), ("max_preis", "99.9"), ("max_preis", "12.50"),
                           ("min_rabatt", "0"), ("min_rabatt", "20,5"), ("min_rabatt", "100")):
            with self.subTest(gueltig=(feld, wert)):
                r = pruefe(feld, wert)
                self.assertEqual(r["fehler"], [])
                self.assertEqual(r["alarme"][0][feld], wert)
                # Gegenprobe am Server: dieselbe Grenze wird von /api/suche angenommen.
                status = self.seite.evaluate(
                    "async (q) => (await fetch('/api/suche?' + new URLSearchParams(q))).status", {feld: wert, "text": "X"})
                self.assertEqual(status, 200)

    def test_alarm_anlegen_nur_wenn_wiederherstellbar(self):
        """Was die Wiederherstellung verwerfen würde, wird gar nicht erst angelegt (kein /api/suche-Request)."""
        suchen = []
        self.seite.on("request", lambda r: suchen.append(r.url) if "/api/suche" in r.url else None)
        for text, feld, wert, hinweis in (("Rad", "max_preis", "1.299,99", "Bis €"), ("Rad", "max_preis", "10€", "Bis €"),
                                          ("Rad", "min_rabatt", "12.345", "Ab % billiger"),
                                          ("x" * 201, "max_preis", "5", "200 Zeichen")):
            with self.subTest(feld=feld, wert=wert, laenge=len(text)):
                self.seite.evaluate("document.getElementById('status').textContent = ''")
                self.seite.fill("#text", text)
                self.seite.fill('[name="max_preis"]', wert if feld == "max_preis" else "")
                self.seite.fill('[name="min_rabatt"]', wert if feld == "min_rabatt" else "")
                self.warte("!document.getElementById('alarm-anlegen').disabled")
                # Die verzögerte Filtersuche abwarten, damit sie #status nicht nachträglich überschreibt.
                self.warte("document.getElementById('status').textContent.length > 0")
                self.seite.evaluate("document.getElementById('status').textContent = ''")
                suchen.clear()
                self.seite.click("#alarm-anlegen")
                self.warte("document.getElementById('status').textContent.startsWith('Preisalarm nicht angelegt')")
                self.seite.wait_for_timeout(300)
                self.assertIn(self.stand()[1], (None, []))
                self.assertIn(hinweis, self.seite.locator("#status").text_content())
                # Genau die Anfrage, mit der alarmAnlegen() den Wunsch beim Server prüfen würde
                ziel = self.basis + "/api/suche?" + self.seite.evaluate(
                    "(w) => new URLSearchParams(Object.fromEntries(Object.entries({text: w.text, sortierung: 'preis', "
                    "ohne_veraltet: '1', max_preis: w.max_preis, min_rabatt: w.min_rabatt}).filter(([, v]) => v))).toString()",
                    {"text": text, "max_preis": wert if feld == "max_preis" else "", "min_rabatt": wert if feld == "min_rabatt" else ""})
                self.assertNotIn(ziel, suchen)

    def test_alarm_rundreise_1299_99(self):
        self.seite.fill("#text", "Fernseher")
        self.seite.fill('[name="max_preis"]', "1299,99")
        self.warte("!document.getElementById('alarm-anlegen').disabled")
        self.seite.click("#alarm-anlegen")
        self.warte("JSON.parse(localStorage.getItem('schnapper.alarme')||'[]').length === 1")
        vorher = self.stand()[1]
        self.assertEqual(vorher[0]["max_preis"], "1299,99")
        self.seite.click('[data-ansicht="alarme"]')
        with self.seite.expect_download() as info:
            self.seite.click("#sicherung-export")
        inhalt = pathlib.Path(info.value.path()).read_bytes()
        self.seite.evaluate("localStorage.clear()")
        self.seite.reload()
        self.seite.wait_for_selector("#treffer li")
        self.assertEqual(self.roh(), [None, None])
        self.seite.click('[data-ansicht="alarme"]')
        meldung = self.lade(inhalt)
        self.assertIn("Wiederhergestellt: 0 gemerkt, 1 Alarme; 0 ungültige Einträge übersprungen", meldung)
        self.assertEqual(self.stand()[1], vorher)

    def test_rundreise_url_schema_grossgeschrieben(self):
        """Eine selbst exportierte Sicherung mit HTTPS://… bzw. Https://… ergibt nach Leeren denselben Stand."""
        start = {"gross": merk("Rad gross", url="HTTPS://beispiel.example/gross"),
                 "misch": merk("Rad misch", url="Https://beispiel.example/misch")}
        self.seite.evaluate("m => localStorage.setItem('schnapper.merkliste', JSON.stringify(m))", start)
        self.seite.reload()
        self.seite.wait_for_selector("#treffer li")
        vorher = self.stand()[0]
        self.assertEqual(vorher, start)
        self.seite.click('[data-ansicht="alarme"]')
        with self.seite.expect_download() as info:
            self.seite.click("#sicherung-export")
        inhalt = pathlib.Path(info.value.path()).read_bytes()
        self.assertEqual(json.loads(inhalt)["merkliste"], vorher)
        self.seite.evaluate("localStorage.clear()")
        self.seite.reload()
        self.seite.wait_for_selector("#treffer li")
        self.assertEqual(self.roh(), [None, None])
        self.seite.click('[data-ansicht="alarme"]')
        meldung = self.lade(inhalt)
        self.assertIn("Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen", meldung)
        self.assertEqual(self.fehlerliste(), [])
        nachher = self.stand()[0]
        self.assertEqual(nachher, vorher)
        self.assertEqual(nachher["gross"]["url"], "HTTPS://beispiel.example/gross")
        self.assertEqual(nachher["misch"]["url"], "Https://beispiel.example/misch")

    def test_url_anderes_schema_grossgeschrieben_bleibt_ungueltig(self):
        """Abgrenzung: Das i-Flag lässt nur http(s) zu, JAVASCRIPT: bleibt ungültig (url)."""
        self.seite.click('[data-ansicht="alarme"]')
        meldung = self.lade(sicherung(merkliste={"js-gross": merk(url="JAVASCRIPT:alert(1)"),
                                                 "gut": merk(url="HTTPS://beispiel.example/ok")}))
        self.assertIn("Wiederhergestellt: 1 gemerkt, 0 Alarme; 1 ungültige Einträge übersprungen", meldung)
        fehler = self.fehlerliste()
        self.assertEqual(len(fehler), 1)
        self.assertIn("„js-gross“ ungültig (url)", fehler[0])
        self.assertEqual(sorted(self.stand()[0]), ["gut"])

    def test_gueltige_alarme_weiter_anlegbar(self):
        for i, (feld, wert) in enumerate((("max_preis", "80"), ("max_preis", "12,50"), ("max_preis", "1299,99"),
                                          ("min_rabatt", "20,5")), 1):
            with self.subTest(feld=feld, wert=wert):
                self.seite.fill("#text", f"Ding{i}")
                self.seite.fill('[name="max_preis"]', wert if feld == "max_preis" else "")
                self.seite.fill('[name="min_rabatt"]', wert if feld == "min_rabatt" else "")
                self.warte("!document.getElementById('alarm-anlegen').disabled")
                self.seite.click("#alarm-anlegen")
                self.warte(f"JSON.parse(localStorage.getItem('schnapper.alarme')||'[]').length === {i}")
                self.assertTrue(self.seite.locator("#status").text_content().startswith("Preisalarm angelegt"))


class ServerUrlSchema(unittest.TestCase):
    def test_server_nimmt_grossgeschriebenes_schema_unveraendert_an(self):
        """Beleg: Der Server akzeptiert HTTPS://… und reicht die URL unverändert weiter."""
        import datetime as dt
        from schnapper.angebot import Angebot
        jetzt = dt.datetime(2026, 10, 29, 12, 0, tzinfo=dt.timezone.utc)
        for url in ("HTTPS://beispiel.example/x", "Https://beispiel.example/y"):
            with self.subTest(url):
                angebot = Angebot.aus_dict({"id": "x", "titel": "Rad", "preis": "10", "url": url,
                                            "quelle": "beispielmarkt", "erfasst_am": "2026-10-29T10:00:00Z"}, jetzt)
                self.assertEqual(angebot.url, url)


if __name__ == "__main__":
    unittest.main()
