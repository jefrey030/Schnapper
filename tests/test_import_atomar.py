"""Regression: Ein fehlgeschlagener Verlaufsspeicher darf keinen Import aktivieren.

Kein Netzwerk, keine Cloud und keine kostenpflichtigen Dienste.
"""
import json
import pathlib
import tempfile
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import Importergebnis  # noqa: E402
from schnapper.quellen import Register  # noqa: E402
from schnapper.web import Zustand, baue_handler  # noqa: E402
from schnapper.angebot import Angebot, normalisiere_url  # noqa: E402
from schnapper.verlauf import Verlauf  # noqa: E402


class ImportZustand(unittest.TestCase):
    def setUp(self):
        self.alt = Importergebnis()
        self.neu = Importergebnis()
        self.zustand = Zustand(Register(), self.alt, "vorher.csv", True)

    def test_speicherfehler_aktiviert_neue_liste_nicht(self):
        with mock.patch.object(self.zustand, "preise_merken", side_effect=OSError("Festplatte voll")):
            with self.assertRaises(OSError):
                self.zustand.ersetzen(self.neu, "neu.csv")
        daten, name, beispiel = self.zustand.lesen()
        self.assertIs(daten, self.alt)
        self.assertEqual(name, "vorher.csv")
        self.assertTrue(beispiel)

    def test_liste_wird_erst_nach_gespeichertem_verlauf_aktiviert(self):
        def pruefe_reihenfolge(geladen):
            self.assertIs(geladen, self.neu)
            daten, name, beispiel = self.zustand.lesen()
            self.assertIs(daten, self.alt)
            self.assertEqual(name, "vorher.csv")
            self.assertTrue(beispiel)

        with mock.patch.object(self.zustand, "preise_merken", side_effect=pruefe_reihenfolge) as speichern:
            self.zustand.ersetzen(self.neu, "neu.csv")
            speichern.assert_called_once_with(self.neu)
        daten, name, beispiel = self.zustand.lesen()
        self.assertIs(daten, self.neu)
        self.assertEqual(name, "neu.csv")
        self.assertFalse(beispiel)

    def test_erneuter_import_speichert_nach_frueherem_fehler_auch_ohne_neue_punkte(self):
        verlauf = mock.Mock()
        verlauf.importiere.side_effect = [OSError("Festplatte voll"), 0]
        self.zustand.verlauf = verlauf

        with self.assertRaises(OSError):
            self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertIs(self.zustand.lesen()[0], self.alt)

        # Ein neuer Import nach dem Schreibfehler muss die Persistenz
        # nochmals ausführen; im echten Verlauf werden Fehler rückgängig gemacht.
        self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertEqual(verlauf.importiere.call_count, 2)
        self.assertIs(self.zustand.lesen()[0], self.neu)

    def test_ohne_verlauf_bleibt_import_moeglich(self):
        self.zustand.ersetzen(self.neu, "neu.csv")
        self.assertIs(self.zustand.lesen()[0], self.neu)


    def test_parallele_importe_werden_serialisiert(self):
        """Langsames Speichern darf einen späteren Import nicht überholen."""
        zweiter = Importergebnis()
        im_ersten_speichern = threading.Event()
        erster_darf_weiter = threading.Event()
        zweiter_gestartet = threading.Event()
        zweiter_speichert = threading.Event()
        fehler = []

        def speichern(geladen):
            if geladen is self.neu:
                im_ersten_speichern.set()
                if not erster_darf_weiter.wait(timeout=3):
                    raise TimeoutError("Erster Import blieb blockiert")
            if geladen is zweiter:
                zweiter_speichert.set()

        def lauf(geladen, name):
            try:
                self.zustand.ersetzen(geladen, name)
            except Exception as exc:
                fehler.append(exc)

        def spaeter():
            zweiter_gestartet.set()
            lauf(zweiter, "zweiter.csv")

        with mock.patch.object(self.zustand, "preise_merken", side_effect=speichern):
            a = threading.Thread(target=lauf, args=(self.neu, "erster.csv"))
            b = threading.Thread(target=spaeter)
            a.start()
            try:
                self.assertTrue(im_ersten_speichern.wait(2), "Erster Import wurde nicht gestartet")
                b.start()
                self.assertTrue(zweiter_gestartet.wait(2))
                b.join(timeout=0.1)
                self.assertFalse(zweiter_speichert.is_set(), "Zweiter Import hat ersten überholt")
                self.assertEqual(self.zustand.lesen()[1], "vorher.csv")
            finally:
                erster_darf_weiter.set()
                a.join(timeout=3)
                if b.ident is not None:
                    b.join(timeout=3)
        self.assertFalse(a.is_alive())
        self.assertFalse(b.is_alive())
        self.assertFalse(fehler, str(fehler))
        self.assertTrue(zweiter_speichert.is_set())
        self.assertEqual(self.zustand.lesen()[1], "zweiter.csv")


class ImportHTTPRegression(unittest.TestCase):
    """Testet den echten lokalen HTTP-Fehlerpfad, ohne das Internet."""

    def test_speicherfehler_antwortet_500_und_behaelt_bisherige_liste(self):
        alt = Importergebnis()
        zustand = Zustand(Register(), alt, "bisher.csv", True)
        server = ThreadingHTTPServer(("127.0.0.1", 0), baue_handler(zustand))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        basis = f"http://127.0.0.1:{server.server_address[1]}"
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        payload = (
            "id;titel;preis;url;quelle;erfasst_am\\n"
            "e1;Lampe;19;https://shop.example/l;eigene;2026-10-21T20:00:00Z\\n"
        ).replace("\\\\n", "\\n").encode("utf-8")
        try:
            request = urllib.request.Request(
                basis + "/api/import", data=payload, method="POST",
                headers={"X-Schnapper": "1", "X-Dateiname": "neu.csv",
                         "Content-Type": "text/csv"})
            with mock.patch.object(zustand, "preise_merken", side_effect=OSError("voll")):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    opener.open(request, timeout=5)
            self.assertEqual(caught.exception.code, 500)
            fehler = json.loads(caught.exception.read().decode("utf-8"))["fehler"]
            self.assertIn("nicht übernommen", fehler)
            self.assertNotIn("Liste geladen", fehler)
            with opener.open(basis + "/api/suche", timeout=5) as response:
                daten = json.loads(response.read())
            self.assertEqual(daten["liste"], "bisher.csv")
            self.assertTrue(daten["beispieldaten"])
            self.assertEqual(daten["eingelesen"], 0)
            self.assertIs(zustand.lesen()[0], alt)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class VerlaufTransaktion(unittest.TestCase):
    @staticmethod
    def angebot(tag, preis):
        return Angebot.aus_dict({
            "id": f"t{tag}", "titel": "Testprodukt", "preis": str(preis),
            "url": "https://shop.example/item/7", "quelle": "mock",
            "erfasst_am": f"2026-10-{tag:02d}T12:00:00Z",
        })

    def test_schreibfehler_rollt_preisverlauf_im_ram_zurueck(self):
        with tempfile.TemporaryDirectory() as tmp:
            verlauf = Verlauf(pathlib.Path(tmp, "preise.json"))
            erst = self.angebot(20, 39)
            spaeter = self.angebot(21, 25)
            self.assertEqual(verlauf.importiere([erst]), 1)
            inhalt_davor = verlauf.pfad.read_bytes()
            with mock.patch.object(verlauf, "speichern", side_effect=OSError("Datenträger voll")):
                with self.assertRaises(OSError):
                    verlauf.importiere([spaeter])
            eintraege = verlauf._daten[normalisiere_url(erst.url)]
            self.assertEqual(len(eintraege), 1)
            self.assertEqual(eintraege[0][1], erst.gesamtpreis)
            self.assertEqual(verlauf.pfad.read_bytes(), inhalt_davor)
            self.assertEqual(verlauf.importiere([spaeter]), 1)
            self.assertEqual(len(verlauf._daten[normalisiere_url(erst.url)]), 2)

    def test_erneuter_identischer_import_speichert_trotz_null_neuer_punkte(self):
        with tempfile.TemporaryDirectory() as tmp:
            verlauf = Verlauf(pathlib.Path(tmp, "preise.json"))
            angebot = self.angebot(20, 39)
            self.assertEqual(verlauf.importiere([angebot]), 1)
            with mock.patch.object(verlauf, "speichern", wraps=verlauf.speichern) as speichern:
                self.assertEqual(verlauf.importiere([angebot]), 0)
                speichern.assert_called_once()


if __name__ == "__main__":
    unittest.main()
