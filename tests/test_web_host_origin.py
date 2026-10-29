"""MASTER 10: lokale Web-Origin/Host-Prüfung mit echten Loopback-HTTP-Anfragen.

Keine externen Netzwerke, keine Modellaufrufe, keine Datenänderungen auf main.
"""
from __future__ import annotations

import http.client
import json
import pathlib
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper.einlesen import Importergebnis
from schnapper.quellen import Register
from schnapper.web import Zustand, _lokaler_host, _origin_erlaubt, baue_handler


class LocalAddressPolicyTests(unittest.TestCase):
    def test_loopback_and_localhost_on_exact_port(self):
        self.assertEqual(_lokaler_host("127.0.0.1:8765", "127.0.0.1", 8765),
                         ("127.0.0.1", 8765))
        self.assertEqual(_lokaler_host("localhost:8765", "127.0.0.1", 8765),
                         ("localhost", 8765))
        self.assertIsNone(_lokaler_host("localhost:9999", "127.0.0.1", 8765))

    def test_dns_rebinding_like_foreign_hostname_is_denied(self):
        for host in ("evil.example:8765", "myrouter.local:8765",
                     "attacker.example@127.0.0.1:8765",
                     "127.0.0.1:8765/evil", "127.0.0.1:8765@evil.example"):
            with self.subTest(host=host):
                self.assertIsNone(_lokaler_host(host, "127.0.0.1", 8765))

    def test_private_lan_ip_only_if_explicit_network_bind(self):
        self.assertEqual(_lokaler_host("192.168.1.20:8765", "0.0.0.0", 8765),
                         ("192.168.1.20", 8765))
        self.assertIsNone(_lokaler_host("192.168.1.20:8765", "127.0.0.1", 8765))
        self.assertIsNone(_lokaler_host("8.8.8.8:8765", "0.0.0.0", 8765))

    def test_origin_must_match_request_host_and_port(self):
        self.assertTrue(_origin_erlaubt("http://127.0.0.1:8765", "127.0.0.1", 8765))
        self.assertTrue(_origin_erlaubt(None, "127.0.0.1", 8765))
        for origin in ("https://127.0.0.1:8765",
                       "http://fremd.example:8765",
                       "http://127.0.0.1:8766", "null",
                       "http://127.0.0.1:8765/fremd"):
            with self.subTest(origin=origin):
                self.assertFalse(_origin_erlaubt(origin, "127.0.0.1", 8765))


class LocalHttpSecurityTests(unittest.TestCase):
    """Tests kommunizieren ausschließlich über ein kurzlebiges Loopback-Socket."""

    @classmethod
    def setUpClass(cls):
        zustand = Zustand(Register(), Importergebnis(), "leer.json", False)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), baue_handler(zustand))
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, method, path, host, origin=None):
        headers = {"Host": host}
        if origin is not None:
            headers["Origin"] = origin
        body = None
        if method == "POST":
            body = b'{"angebote":[]}'
            headers.update({"X-Schnapper": "1", "X-Dateiname": "leer.json",
                            "Content-Type": "application/octet-stream"})
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers)
            result = connection.getresponse()
            data = result.read()
            return result.status, json.loads(data)
        finally:
            connection.close()

    def test_real_http_local_search_remains_available(self):
        code, data = self.request("GET", "/api/suche", f"127.0.0.1:{self.port}")
        self.assertEqual(code, 200)
        self.assertEqual(data["treffer"], [])

    def test_real_http_foreign_host_cannot_read_list(self):
        code, data = self.request("GET", "/api/suche", f"evil.example:{self.port}")
        self.assertEqual(code, 403)
        self.assertIn("Host", data["fehler"])

    def test_real_http_foreign_origin_cannot_import(self):
        code, data = self.request("POST", "/api/import",
                                  f"127.0.0.1:{self.port}", "http://evil.example")
        self.assertEqual(code, 403)
        self.assertIn("Fremde", data["fehler"])

    def test_real_http_same_origin_import_reaches_validation(self):
        code, data = self.request("POST", "/api/import",
                                  f"127.0.0.1:{self.port}",
                                  f"http://127.0.0.1:{self.port}")
        self.assertEqual(code, 422)  # leere Testliste: kein zulässiges Angebot
        self.assertIn("Keine gültigen", data["fehler"])


if __name__ == "__main__":
    unittest.main()
