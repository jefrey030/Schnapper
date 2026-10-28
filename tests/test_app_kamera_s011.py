"""Tests für S-011 / F4: Barcode per Kamera scannen (BarcodeDetector), rein im Browser."""
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

# Stand von main (6dbe114): die CSP bleibt für S-011 unverändert.
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'self' data:; manifest-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")

NICHT_UNTERSTUETZT = "Kamera-Scan wird von diesem Browser nicht unterstützt – bitte Barcode eintippen."
ZEITLIMIT = "Kein Barcode erkannt – bitte erneut versuchen oder eintippen."

# Simulierte Kamera: ein Canvas-Stream statt echter Kamera, Zähler für Aufrufe und gestoppte Tracks.
MEDIEN = """
(() => {
  window.__gum = 0; window.__gestoppt = 0; window.__tracks = [];
  const fehler = %(fehler)s;
  const md = navigator.mediaDevices || {};
  md.getUserMedia = async (vorgabe) => {
    window.__gum++;
    window.__vorgabe = JSON.stringify(vorgabe);
    if (fehler) throw new DOMException("simuliert", fehler);
    const c = document.createElement("canvas");
    c.width = 64; c.height = 48;
    const g = c.getContext("2d"); g.fillStyle = "#888"; g.fillRect(0, 0, 64, 48);
    const s = c.captureStream(10);
    for (const t of s.getTracks()) {
      const stop = t.stop.bind(t);
      t.stop = () => { window.__gestoppt++; stop(); };
      window.__tracks.push(t);
    }
    return s;
  };
  if (!navigator.mediaDevices) Object.defineProperty(navigator, "mediaDevices", { value: md, configurable: true });
})();
"""

DETEKTOR = """
(() => {
  window.__detect = 0;
  const modus = %(modus)s;
  window.BarcodeDetector = class {
    constructor(opt) { window.__formate = JSON.stringify(opt && opt.formats); }
    static async getSupportedFormats() { return ["ean_13", "ean_8", "upc_a", "qr_code"]; }
    async detect(quelle) {
      window.__detect++;
      if (modus === "treffer" && window.__detect >= 2) return [{ rawValue: "4008400402222", format: "ean_13" }];
      return [];
    }
  };
})();
"""

OHNE_DETEKTOR = "delete window.BarcodeDetector;"

# Verzögerte Formatabfrage (nach DETEKTOR einbinden): der 1. Aufruf (kameraVerfuegbar() beim Laden)
# löst sofort auf, ab dem 2. Aufruf erst auf Kommando __formateAufloesen(i) (i zählt ab dem 2. Aufruf).
FORMATE_VERZOEGERT = """
(() => {
  window.__formatAufrufe = 0; window.__formatAnfragen = [];
  const LISTE = ["ean_13", "ean_8", "upc_a", "qr_code"];
  window.BarcodeDetector.getSupportedFormats = () => {
    window.__formatAufrufe++;
    if (window.__formatAufrufe === 1) return Promise.resolve(LISTE.slice());
    return new Promise((ja) => window.__formatAnfragen.push(ja));
  };
  window.__formateAufloesen = (i) => window.__formatAnfragen[i](LISTE.slice());
})();
"""

# Verzögerte Kamera: getUserMedia löst erst auf Kommando auf (wie ein offener Berechtigungsdialog).
# __aufloesen(i) liefert den Stream für Anfrage i, __ablehnen(i, name) lehnt sie mit DOMException ab.
MEDIEN_VERZOEGERT = """
(() => {
  window.__gum = 0; window.__gestoppt = 0; window.__tracks = []; window.__streams = []; window.__anfragen = [];
  const md = navigator.mediaDevices || {};
  md.getUserMedia = (vorgabe) => {
    window.__gum++;
    return new Promise((ja, nein) => window.__anfragen.push({ ja, nein }));
  };
  window.__aufloesen = (i) => {
    const c = document.createElement("canvas");
    c.width = 64; c.height = 48;
    const g = c.getContext("2d"); g.fillStyle = "#888"; g.fillRect(0, 0, 64, 48);
    const s = c.captureStream(10);
    for (const t of s.getTracks()) {
      const stop = t.stop.bind(t);
      t.stop = () => { window.__gestoppt++; stop(); };
      window.__tracks.push(t);
    }
    window.__streams[i] = s;
    window.__anfragen[i].ja(s);
  };
  window.__ablehnen = (i, name) => window.__anfragen[i].nein(new DOMException("simuliert", name));
  if (!navigator.mediaDevices) Object.defineProperty(navigator, "mediaDevices", { value: md, configurable: true });
})();
"""


class Statisch(unittest.TestCase):
    """AK1, AK9, AK10, AK11: Markup, keine Bildspeicherung, kein innerHTML, CSP unverändert."""

    def test_markup(self):
        html = (WEB / "index.html").read_text(encoding="utf-8")
        for teil in ('<button id="kamera-knopf" type="button" disabled>Mit Kamera scannen</button>',
                     '<div id="kamera-bereich" hidden>', '<video id="kamera-bild" muted playsinline></video>',
                     '<button id="kamera-abbrechen" type="button" hidden>Abbrechen</button>',
                     '<p id="kamera-status" class="status" aria-live="polite"></p>',
                     'id="barcode" inputmode="numeric"', 'id="barcode-knopf" type="submit"', 'id="barcode-form"'):
            self.assertIn(teil, html)
        # Abbrechen liegt außerhalb des (bis zum Kamerastart verborgenen) Videobereichs.
        bereich = html[html.index('<div id="kamera-bereich" hidden>'):]
        bereich = bereich[:bereich.index("</div>")]
        self.assertNotIn("kamera-abbrechen", bereich)

    def test_app_js(self):
        js = (WEB / "app.js").read_text(encoding="utf-8")
        code = "\n".join(re.sub(r"//.*$", "", z) for z in js.splitlines())
        self.assertNotIn("innerHTML", code)
        self.assertIn('const KAMERA_FORMATE = ["ean_13", "ean_8", "upc_a"];', js)
        self.assertIn("const KAMERA_ZEITLIMIT = 20000;", js)
        start = js.index("// ---------- Kamera-Scan")
        kamera = js[start:js.index("// ---------- Preisalarm", start)]
        for verboten in ("createObjectURL", "toDataURL", "toBlob", "getImageData", "localStorage", "fetch(",
                         "console.", "innerHTML", "http://", "https://"):
            self.assertNotIn(verboten, kamera)
        self.assertIn("getTracks().forEach((t) => t.stop())", kamera)

    def test_csp_unveraendert(self):
        self.assertEqual(SICHERHEIT["Content-Security-Policy"], CSP)
        self.assertNotIn("Permissions-Policy", SICHERHEIT)

    def test_chromium_suche(self):
        with tempfile.TemporaryDirectory() as tmp:
            basis = pathlib.Path(tmp)
            self.assertIsNone(_finde_chromium(basis))
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
        self.meldungen, self.fremd, self.abfragen = [], [], []
        self.kontext = self.browser.new_context(viewport={"width": 390, "height": 844})
        # AK9: nur der lokale Server; alles andere wird blockiert und protokolliert.
        self.kontext.route(re.compile(r"^(?!" + re.escape(self.basis) + ").*"), lambda r: r.abort())
        self.seite = self.kontext.new_page()
        # Lokale Barcode-Suche abfangen, damit der Server keine echte Preisquelle anfragt.
        self.seite.route(self.basis + "/api/openprices", self.openprices)
        self.seite.on("request", lambda r: None if r.url.startswith(self.basis + "/") else self.fremd.append(r.url))
        self.seite.on("console", lambda m: self.meldungen.append(m.text) if m.type == "error" else None)
        self.seite.on("pageerror", lambda e: self.meldungen.append(str(e)))

    def tearDown(self):
        self.kontext.close()
        self.server.shutdown()
        self.server.server_close()
        self.assertEqual(self.fremd, [])
        self.assertEqual(self.meldungen, [])

    def openprices(self, route):
        self.abfragen.append(json.loads(route.request.post_data or "{}"))
        route.fulfill(status=200, content_type="application/json; charset=utf-8",
                      body=json.dumps({"treffer": [], "lizenz": "", "begrenzung": "", "hinweise": []}))

    # ---------- Hilfen ----------
    def oeffne(self, detektor="treffer", fehler=None, uhr=False, verzoegert=False, formate_verzoegert=False):
        if detektor is None:
            self.seite.add_init_script(OHNE_DETEKTOR)
        else:
            self.seite.add_init_script(DETEKTOR % {"modus": json.dumps(detektor)})
            if formate_verzoegert:
                self.seite.add_init_script(FORMATE_VERZOEGERT)
        self.seite.add_init_script(MEDIEN_VERZOEGERT if verzoegert else MEDIEN % {"fehler": json.dumps(fehler)})
        if uhr:
            self.seite.clock.install()
        self.seite.goto(self.basis + "/")
        self.seite.wait_for_selector("#treffer li")

    def warte(self, ausdruck, sekunden=10):
        """Wie wait_for_function, aber ohne eval im Seitenkontext (die CSP verbietet 'unsafe-eval')."""
        ende = time.monotonic() + sekunden
        while not self.seite.evaluate(ausdruck):
            if time.monotonic() > ende:
                self.fail("Zeitüberschreitung: " + ausdruck)
            time.sleep(0.05)

    def wert(self, ausdruck):
        return self.seite.evaluate(ausdruck)

    def status(self):
        return self.seite.locator("#kamera-status").text_content()

    def kein_quer_scrollen(self):
        self.assertLessEqual(self.wert("document.documentElement.scrollWidth"), 390)

    def alles_gestoppt(self):
        self.assertGreater(self.wert("window.__tracks.length"), 0)
        self.assertEqual(self.wert("window.__gestoppt"), self.wert("window.__tracks.length"))
        self.assertTrue(self.wert("window.__tracks.every((t) => t.readyState === 'ended')"))
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === null"))
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))

    def abbrechen_sichtbar(self):
        """Abbrechen ist sofort sichtbar, das Video (noch) nicht."""
        self.assertTrue(self.seite.locator("#kamera-abbrechen").is_visible())
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertFalse(self.seite.locator("#kamera-bild").is_visible())

    def verstecken(self):
        """Seite in den Hintergrund: visibilityState 'hidden' plus visibilitychange, danach wieder sichtbar."""
        self.wert("""(() => {
          Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });
          document.dispatchEvent(new Event('visibilitychange'));
          delete document.visibilityState;
        })()""")

    def kurz_warten(self):
        self.wert("new Promise((r) => setTimeout(r, 100))")

    def starte(self):
        self.warte("!document.getElementById('kamera-knopf').disabled")
        self.assertEqual(self.wert("window.__gum"), 0)  # AK1: erst nach Klick
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())  # Ruhezustand
        self.seite.click("#kamera-knopf")

    # ---------- Tests ----------
    def test_ak1_ak2_ak3_treffer_fuellt_feld(self):
        self.oeffne("treffer")
        self.assertEqual(self.seite.locator("#kamera-knopf").text_content(), "Mit Kamera scannen")
        self.kein_quer_scrollen()
        self.starte()
        self.warte("document.getElementById('barcode').value === '4008400402222'")
        self.warte("document.getElementById('barcode-status').textContent === 'Keine passenden gemeldeten Preise gefunden.'")
        self.assertEqual(self.abfragen, [{"ean": "4008400402222"}])
        self.assertEqual(self.wert("window.__gum"), 1)
        self.assertEqual(json.loads(self.wert("window.__vorgabe")), {"video": {"facingMode": "environment"}, "audio": False})
        self.assertEqual(json.loads(self.wert("window.__formate")), ["ean_13", "ean_8", "upc_a"])
        self.alles_gestoppt()
        self.assertIn("4008400402222", self.status())
        self.kein_quer_scrollen()

    def test_ak4_abbrechen(self):
        self.oeffne("leer")
        self.starte()
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))  # kein Doppelstart
        self.assertTrue(self.seite.locator("#kamera-bild").is_visible())
        self.assertTrue(self.seite.locator("#kamera-abbrechen").is_visible())
        self.kein_quer_scrollen()
        self.seite.click("#kamera-abbrechen")
        self.alles_gestoppt()
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")
        self.assertEqual(self.seite.input_value("#barcode"), "")
        self.assertEqual(self.abfragen, [])
        # Zweiter Start nach Abbruch funktioniert und stoppt wieder sauber.
        self.seite.click("#kamera-knopf")
        self.warte("!document.getElementById('kamera-bereich').hidden")
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.wert("window.__gum"), 2)
        self.alles_gestoppt()

    def test_ak5_zeitlimit(self):
        self.oeffne("leer", uhr=True)
        self.starte()
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.seite.clock.run_for(19000)
        self.assertFalse(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.seite.clock.run_for(2000)
        self.warte("document.getElementById('kamera-bereich').hidden")
        self.alles_gestoppt()
        self.assertEqual(self.status(), ZEITLIMIT)
        self.assertEqual(self.abfragen, [])

    def test_ak6_ohne_barcodedetector(self):
        self.oeffne(None)
        self.warte("document.getElementById('kamera-status').textContent.length > 0")
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertEqual(self.status(), NICHT_UNTERSTUETZT)
        self.assertTrue(self.seite.locator("#kamera-status").is_visible())
        self.assertEqual(self.wert("window.__gum"), 0)
        # Handeingabe bleibt möglich.
        self.seite.fill("#barcode", "4008400402222")
        self.seite.click("#barcode-knopf")
        self.warte("document.getElementById('barcode-status').textContent === 'Keine passenden gemeldeten Preise gefunden.'")
        self.assertEqual(self.abfragen, [{"ean": "4008400402222"}])
        self.kein_quer_scrollen()

    def test_ak6_ohne_mediadevices(self):
        self.seite.add_init_script("Object.defineProperty(navigator, 'mediaDevices', { value: undefined, configurable: true });")
        self.seite.add_init_script(DETEKTOR % {"modus": json.dumps("treffer")})
        self.seite.goto(self.basis + "/")
        self.seite.wait_for_selector("#treffer li")
        self.warte("document.getElementById('kamera-status').textContent.length > 0")
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertEqual(self.status(), NICHT_UNTERSTUETZT)

    def fehlerfall(self, name, text):
        self.oeffne("treffer", fehler=name)
        self.starte()
        self.warte(f"document.getElementById('kamera-status').textContent === {json.dumps(text)}")
        self.assertEqual(self.wert("window.__gum"), 1)
        self.assertEqual(self.wert("window.__tracks.length"), 0)  # kein Stream offen
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === null"))
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.seite.fill("#barcode", "40084004")
        self.seite.click("#barcode-knopf")
        self.warte("document.getElementById('barcode-status').textContent === 'Keine passenden gemeldeten Preise gefunden.'")
        self.assertEqual(self.abfragen, [{"ean": "40084004"}])

    def test_ak7_verweigert(self):
        self.fehlerfall("NotAllowedError", "Kamerazugriff verweigert – Barcode bitte eintippen.")

    def test_ak7_keine_kamera(self):
        self.fehlerfall("NotFoundError", "Keine Kamera gefunden – Barcode bitte eintippen.")

    # ---------- Neustart während offener Kamera-Anfrage (Lauf-ID) ----------
    def neustart_waehrend_anfrage(self):
        """Klick, Seite versteckt (Lauf 1 abgebrochen), zweiter Klick: zwei offene getUserMedia-Anfragen."""
        self.oeffne("leer", verzoegert=True)
        self.starte()
        self.warte("window.__gum === 1")
        self.verstecken()
        self.assertEqual(self.status(), "Kamera-Scan beendet.")
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.seite.click("#kamera-knopf")
        self.warte("window.__gum === 2")

    def test_neustart_alter_stream_sofort_gestoppt(self):
        self.neustart_waehrend_anfrage()
        self.wert("window.__aufloesen(0)")
        # Stream aus Anfrage 1 ist sofort nach seiner Auflösung beendet, nicht erst nach dem Abbrechen.
        self.warte("window.__streams[0].getTracks().every((t) => t.readyState === 'ended')", sekunden=3)
        self.assertEqual(self.wert("window.__gestoppt"), 1)
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.wert("window.__aufloesen(1)")
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        # Lauf 2 ist ungestört aktiv.
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === window.__streams[1]"))
        self.assertTrue(self.wert("window.__streams[1].getTracks().every((t) => t.readyState === 'live')"))
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertEqual(self.status(), "Barcode vor die Kamera halten …")
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.wert("window.__gum"), 2)
        self.assertEqual(self.wert("window.__tracks.length"), 2)
        self.assertEqual(self.wert("window.__gestoppt"), 2)
        self.alles_gestoppt()
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")

    def test_neustart_alter_fehler_stoert_nicht(self):
        self.neustart_waehrend_anfrage()
        self.wert("window.__aufloesen(1)")
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.wert("window.__ablehnen(0, 'NotAllowedError')")
        self.kurz_warten()
        self.assertFalse(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === window.__streams[1]"))
        self.assertTrue(self.wert("window.__streams[1].getTracks().every((t) => t.readyState === 'live')"))
        self.assertEqual(self.wert("window.__gestoppt"), 0)
        self.assertTrue(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertNotIn("Kamerazugriff verweigert", self.status())
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.wert("window.__tracks.length"), 1)
        self.alles_gestoppt()

    # ---------- Abbruch/Neustart während offener Formatabfrage ----------
    def test_abbrechen_waehrend_formatabfrage(self):
        """Fall A: Abbrechen, während getSupportedFormats() noch offen ist; danach löst sie auf."""
        self.oeffne("leer", formate_verzoegert=True)
        self.starte()
        self.warte("window.__formatAnfragen.length === 1")
        self.assertEqual(self.wert("window.__gum"), 1)
        self.abbrechen_sichtbar()
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())
        self.wert("window.__formateAufloesen(0)")
        self.kurz_warten()
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === null"))
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")
        self.assertEqual(self.wert("window.__detect"), 0)
        self.alles_gestoppt()

    # ---------- Abbruch während offener Kamera-Anfrage (Berechtigungsdialog) ----------
    def test_abbrechen_waehrend_kamera_anfrage(self):
        """getUserMedia offen: Abbrechen sofort sichtbar und per echtem Klick bedienbar; später Stream wird gestoppt."""
        self.oeffne("leer", verzoegert=True)
        self.starte()
        self.warte("window.__gum === 1")
        self.assertEqual(self.status(), "Kamera wird gestartet …")
        self.abbrechen_sichtbar()
        self.kein_quer_scrollen()
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())
        # Berechtigung wird nachträglich erteilt: der späte Stream wird sofort beendet.
        self.wert("window.__aufloesen(0)")
        self.warte("window.__streams[0].getTracks().every((t) => t.readyState === 'ended')", sekunden=3)
        self.kurz_warten()
        self.alles_gestoppt()
        self.assertEqual(self.wert("window.__detect"), 0)
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")

    def test_abbrechen_waehrend_kamera_anfrage_spaeter_fehler(self):
        """getUserMedia offen, Abbrechen, danach lehnt die Anfrage ab: Meldung bleibt, nichts wird angezeigt."""
        self.oeffne("leer", verzoegert=True)
        self.starte()
        self.warte("window.__gum === 1")
        self.abbrechen_sichtbar()
        self.seite.click("#kamera-abbrechen")
        self.wert("window.__ablehnen(0, 'NotAllowedError')")
        self.kurz_warten()
        self.assertEqual(self.status(), "Kamera-Scan abgebrochen.")
        self.assertFalse(self.seite.locator("#kamera-abbrechen").is_visible())
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertFalse(self.wert("document.getElementById('kamera-knopf').disabled"))
        self.assertEqual(self.wert("window.__tracks.length"), 0)

    def test_neustart_waehrend_formatabfrage(self):
        """Fall B: Seite versteckt und Neustart bei offener Formatabfrage von Lauf 1; Lauf 2 löst zuerst auf."""
        self.oeffne("leer", formate_verzoegert=True)
        self.starte()
        self.warte("window.__formatAnfragen.length === 1")
        self.verstecken()
        self.assertEqual(self.status(), "Kamera-Scan beendet.")
        self.seite.click("#kamera-knopf")
        self.warte("window.__formatAnfragen.length === 2")
        self.assertEqual(self.wert("window.__gum"), 2)
        self.wert("window.__formateAufloesen(1)")
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.wert("window.__formateAufloesen(0)")
        self.kurz_warten()
        # Lauf 2 bleibt angezeigt und aktiv, Lauf 1 ist beendet.
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject !== null"
                                  " && document.getElementById('kamera-bild').srcObject.getTracks()[0] === window.__tracks[1]"))
        self.assertTrue(self.wert("window.__tracks[1].readyState === 'live'"))
        self.assertTrue(self.wert("window.__tracks[0].readyState === 'ended'"))
        self.assertFalse(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertEqual(self.status(), "Barcode vor die Kamera halten …")
        self.assertGreater(self.wert("window.__detect"), 0)
        self.seite.click("#kamera-abbrechen")
        self.assertEqual(self.wert("window.__tracks.length"), 2)
        self.alles_gestoppt()

    def test_verstecken_waehrend_formatabfrage(self):
        """Fall A über den realen Pfad: Seite versteckt (visibilitychange), während getSupportedFormats() offen ist."""
        self.oeffne("leer", formate_verzoegert=True)
        self.starte()
        self.warte("window.__formatAnfragen.length === 1")
        self.assertEqual(self.wert("window.__formatAnfragen.length"), 1)
        self.assertEqual(self.wert("window.__gum"), 1)
        self.verstecken()
        self.assertEqual(self.status(), "Kamera-Scan beendet.")
        self.wert("window.__formateAufloesen(0)")
        self.kurz_warten()
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === null"))
        self.assertEqual(self.status(), "Kamera-Scan beendet.")
        self.assertEqual(self.wert("window.__detect"), 0)
        self.alles_gestoppt()

    def test_pagehide_waehrend_formatabfrage(self):
        """Fall A über den realen Pfad: pagehide, während getSupportedFormats() offen ist."""
        self.oeffne("leer", formate_verzoegert=True)
        self.starte()
        self.warte("window.__formatAnfragen.length === 1")
        self.assertEqual(self.wert("window.__formatAnfragen.length"), 1)
        self.assertEqual(self.wert("window.__gum"), 1)
        self.wert("window.dispatchEvent(new Event('pagehide'))")
        self.wert("window.__formateAufloesen(0)")
        self.kurz_warten()
        self.assertTrue(self.wert("document.getElementById('kamera-bereich').hidden"))
        self.assertTrue(self.wert("document.getElementById('kamera-bild').srcObject === null"))
        self.assertEqual(self.wert("window.__detect"), 0)
        self.alles_gestoppt()

    # ---------- Seite verlassen ----------
    def test_visibilitychange_beendet_scan(self):
        self.oeffne("leer")
        self.starte()
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.verstecken()
        self.assertEqual(self.status(), "Kamera-Scan beendet.")
        self.alles_gestoppt()

    def test_pagehide_beendet_scan(self):
        self.oeffne("leer")
        self.starte()
        self.warte("!document.getElementById('kamera-bereich').hidden && window.__detect > 0")
        self.wert("window.dispatchEvent(new Event('pagehide'))")
        self.alles_gestoppt()


if __name__ == "__main__":
    unittest.main()
