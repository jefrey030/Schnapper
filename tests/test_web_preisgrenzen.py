"""Websuche: Ungueltige Preislimits duerfen keine stillen Leeralarme erzeugen.

Nur Standardbibliothek und lokale HTTP-Tests, keine externen Dienste.
"""
import pathlib
import sys
import threading
import unittest
import urllib.error
import urllib.request
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.web import erstelle_server, filter_aus_query  # noqa: E402


class FilterGrenzen(unittest.TestCase):
    def test_null_und_negative_preise_abweisen(self):
        for wert in ("0", "-1", "-0,01", "0,001", "-10 €"):
            with self.subTest(wert=wert), self.assertRaisesRegex(ValueError, "Höchstpreis"):
                filter_aus_query({"max_preis": [wert]})

    def test_positive_limits_bleiben_gueltig(self):
        for wert, erwartet in (("0,01", "0.01"), ("50", "50.00"), ("75,50", "75.50")):
            with self.subTest(wert=wert):
                f, sortierung = filter_aus_query({"max_preis": [wert]})
                self.assertEqual(f.max_preis, Decimal(erwartet))
                self.assertEqual(sortierung, "rabatt")

    def test_leerer_filter_hat_kein_limit(self):
        f, _ = filter_aus_query({})
        self.assertIsNone(f.max_preis)

    def test_mindestrabatt_bleibt_erhalten(self):
        f, _ = filter_aus_query({"min_rabatt": ["40"]})
        self.assertEqual(f.min_rabatt, Decimal("40"))


class LokaleWebAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = erstelle_server(ROOT / "app" / "beispiele" / "angebote.csv", port=0)
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def status(self, query):
        req = urllib.request.Request(self.url + "/api/suche?" + query)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=5) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code

    def test_web_api_lehnt_null_und_negativ_ab(self):
        for query in ("max_preis=0", "max_preis=-5", "max_preis=-0%2C01"):
            with self.subTest(query=query):
                self.assertEqual(self.status(query), 400)

    def test_web_api_akzeptiert_gueltigen_hoechstpreis(self):
        self.assertEqual(self.status("max_preis=50"), 200)


if __name__ == "__main__":
    unittest.main()
