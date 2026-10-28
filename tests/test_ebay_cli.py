"""Kommandozeile --ebay (S-013): ohne Netzwerk, Transport immer gemockt.

Alle Werte sind erfunden. Echte Socket- und urllib-Aufrufe sind in jedem Test gesperrt.
"""
import io
import json
import os
import pathlib
import socket
import sys
import unittest
import urllib.parse
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import ebay  # noqa: E402
from schnapper.__main__ import main  # noqa: E402

CLIENT_ID = "ID-geheim-123"
SECRET = "SECRET-geheim-456"
TOKEN = "TOK-geheim-xyz"
OHNE = {k: "" for k in (ebay.FREIGABE_VARIABLE, ebay.PRODUKTION_VARIABLE, ebay.ID_VARIABLE, ebay.SECRET_VARIABLE)}
VOLL = {ebay.FREIGABE_VARIABLE: "ja", ebay.ID_VARIABLE: CLIENT_ID, ebay.SECRET_VARIABLE: SECRET}


def _netz_verboten(*a, **k):
    raise AssertionError("Netzaufruf im Test")


def angebot(item_id, titel, preis, waehrung="EUR"):
    return {"itemId": item_id, "title": titel, "price": {"value": preis, "currency": waehrung},
            "itemWebUrl": f"https://www.ebay.de/itm/{item_id}", "conditionId": "3000",
            "shippingOptions": [{"shippingCost": {"value": "4.99", "currency": "EUR"}}]}


SUCHANTWORT = {"itemSummaries": [
    angebot("v1|111|0", "Fahrrad Trekking 28 Zoll", "120.00"),
    angebot("v1|222|0", "Fahrrad Kinder 20 Zoll", "45.00"),
    angebot("v1|333|0", "Fahrrad USA", "99.00", waehrung="USD"),
]}


class Attrappe:
    def __init__(self, fehler=None):
        self.aufrufe = []
        self.fehler = fehler

    def __call__(self, methode, url, kopfzeilen, daten=None, timeout=None):
        teile = urllib.parse.urlsplit(url)
        self.aufrufe.append((methode, teile.hostname, teile.path))
        if self.fehler:
            raise self.fehler
        if methode == "POST" and teile.path == ebay.TOKEN_PFAD:
            return {"access_token": TOKEN, "expires_in": 7200}
        if methode == "GET" and teile.path == ebay.SUCH_PFAD:
            return SUCHANTWORT
        raise AssertionError(f"unerwarteter Aufruf {methode} {teile.path}")


class EbayKommandozeileTests(unittest.TestCase):
    def lauf(self, argv, umgebung=None, attrappe=None):
        out, err = io.StringIO(), io.StringIO()
        with ExitStack() as st:
            st.enter_context(mock.patch("socket.create_connection", _netz_verboten))
            st.enter_context(mock.patch.object(socket.socket, "connect", _netz_verboten))
            st.enter_context(mock.patch("urllib.request.OpenerDirector.open", _netz_verboten))
            st.enter_context(mock.patch.dict("os.environ", OHNE))
            for k in OHNE:  # Rechnerumgebung darf das Ergebnis nicht beeinflussen
                os.environ.pop(k, None)
            if umgebung:
                st.enter_context(mock.patch.dict("os.environ", umgebung))
            if attrappe is not None:
                st.enter_context(mock.patch.object(ebay, "_anfrage", attrappe))
            st.enter_context(redirect_stdout(out))
            st.enter_context(redirect_stderr(err))
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def assertOhneGeheimnisse(self, *texte):
        for t in texte:
            for g in (CLIENT_ID, SECRET, TOKEN):
                self.assertNotIn(g, t)

    # AK 2
    def test_genau_eine_quelle(self):
        for argv in ([], ["x.csv", "--ebay", "foo"], ["--openprices", "4008400402222", "--ebay", "foo"]):
            with self.subTest(argv=argv), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as cm:
                main(argv)
            self.assertEqual(cm.exception.code, 2)

    # Nachbesserung N1: leere EAN darf nicht in lies_datei(None) durchfallen
    def test_openprices_leer_sauberer_fehler(self):
        err = io.StringIO()
        with redirect_stderr(err), self.assertRaises(SystemExit) as cm:
            main(["--openprices", ""])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("--openprices braucht eine EAN", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())

    # AK 3
    def test_ohne_schalter_gesperrt_ohne_netz(self):
        code, out, err = self.lauf(["--ebay", "fahrrad"])
        self.assertEqual(code, 3)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("eBay: "))
        self.assertIn(ebay.FREIGABE_VARIABLE, err)

    # AK 4
    def test_schalter_ohne_secret(self):
        code, out, err = self.lauf(["--ebay", "fahrrad"],
                                   {ebay.FREIGABE_VARIABLE: "ja", ebay.ID_VARIABLE: CLIENT_ID})
        self.assertEqual(code, 3)
        self.assertIn(ebay.SECRET_VARIABLE, err)
        self.assertOhneGeheimnisse(out, err)

    # AK 5
    def test_ungueltiger_suchbegriff(self):
        for begriff in ("", "   ", "x" * 101):
            with self.subTest(laenge=len(begriff)):
                attrappe = Attrappe()
                code, out, err = self.lauf(["--ebay", begriff], VOLL, attrappe)
                self.assertEqual(code, 3)
                self.assertTrue(err.startswith("eBay: "))
                self.assertNotIn("Traceback", err)
                self.assertEqual(attrappe.aufrufe, [])

    # AK 6
    def test_ebay_fehler(self):
        attrappe = Attrappe(fehler=ebay.EbayFehler("eBay HTTP 401 – Zugangsdaten ungültig"))
        code, out, err = self.lauf(["--ebay", "fahrrad"], VOLL, attrappe)
        self.assertEqual(code, 3)
        self.assertIn("eBay: eBay HTTP 401", err)
        self.assertNotIn("Traceback", err)
        self.assertOhneGeheimnisse(out, err)

    # AK 7
    def test_erfolg_sandbox_text(self):
        attrappe = Attrappe()
        code, out, err = self.lauf(["--ebay", "fahrrad"], VOLL, attrappe)
        self.assertEqual(code, 0, err)
        self.assertIn("SANDBOX Fahrrad Trekking 28 Zoll  [ebay]", out)
        self.assertIn("SANDBOX Fahrrad Kinder 20 Zoll  [ebay]", out)
        self.assertIn(ebay.HINWEIS_QUELLE, out)
        self.assertNotIn("USA", out)
        self.assertIn("eBay-Hinweis: ", err)
        self.assertIn("USD", err)
        self.assertEqual({h for _, h, _ in attrappe.aufrufe}, {ebay.SANDBOX_HOST})
        self.assertEqual([m for m, _, _ in attrappe.aufrufe], ["POST", "GET"])
        self.assertOhneGeheimnisse(out, err)

    # AK 8
    def test_erfolg_json(self):
        code, out, err = self.lauf(["--ebay", "fahrrad", "--json"], VOLL, Attrappe())
        self.assertEqual(code, 0, err)
        daten = json.loads(out)
        self.assertEqual(len(daten["treffer"]), 2)
        self.assertTrue(all(t["quelle"] == "ebay" for t in daten["treffer"]))
        self.assertTrue(all(t["titel"].startswith("SANDBOX ") for t in daten["treffer"]))
        self.assertEqual(daten["lizenz"], "Daten: eBay Browse API")
        self.assertNotIn("eBay-Hinweis", out)
        self.assertOhneGeheimnisse(out, err)

    # AK 9
    def test_filter_wirken(self):
        code, out, err = self.lauf(["--ebay", "fahrrad", "--json", "--max-preis", "100"], VOLL, Attrappe())
        self.assertEqual(code, 0, err)
        titel = [t["titel"] for t in json.loads(out)["treffer"]]
        self.assertEqual(titel, ["SANDBOX Fahrrad Kinder 20 Zoll"])
        code, out, err = self.lauf(["--ebay", "fahrrad", "--json", "--suche", "trekking"], VOLL, Attrappe())
        self.assertEqual([t["titel"] for t in json.loads(out)["treffer"]], ["SANDBOX Fahrrad Trekking 28 Zoll"])

    # AK 10
    def test_produktion_nur_mit_schalter(self):
        attrappe = Attrappe()
        code, out, err = self.lauf(["--ebay", "fahrrad", "--json"],
                                   dict(VOLL, **{ebay.PRODUKTION_VARIABLE: "ja"}), attrappe)
        self.assertEqual(code, 0, err)
        self.assertEqual({h for _, h, _ in attrappe.aufrufe}, {ebay.PRODUKTION_HOST})
        self.assertFalse(any(t["titel"].startswith("SANDBOX") for t in json.loads(out)["treffer"]))


if __name__ == "__main__":
    unittest.main()
