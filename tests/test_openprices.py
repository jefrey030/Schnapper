"""Open-Prices-Adapter (Q5): ohne Netzwerk, gegen das dokumentierte Antwortformat.

Feldnamen laut https://openfoodfacts.github.io/documentation/docs/Open-prices/prices/prices_list/
(Stand 22.10.2026). Die Beispielwerte unten sind erfunden; nur die Struktur entspricht der API.
"""
import datetime as dt
import io
import json
import pathlib
import socket
import sys
import unittest
import urllib.parse
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import openprices as op
from schnapper.__main__ import main
from schnapper.adapter import finde
from schnapper.quellen import AUSGESCHLOSSEN, Quelle, Register, STANDARD

EAN = "4008400402222"
FREI = {op.FREIGABE_VARIABLE: "ja"}


def item(pid, preis, datum="2026-10-20", **mehr):
    d = {"id": pid, "type": "PRODUCT", "product_code": EAN, "product_name": "Testschokolade 100 g",
         "price": preis, "price_is_discounted": False, "price_without_discount": None, "price_per": None,
         "currency": "EUR", "date": datum, "duplicate_of": None,
         "location": {"osm_name": "Testmarkt", "osm_address_city": "Berlin", "osm_address_country_code": "DE"},
         "product": {"code": EAN, "product_name": "Testschokolade"}}
    d.update(mehr)
    return d


def antwort(*items):
    return {"items": list(items), "total": len(items), "page": 1, "pages": 1, "size": 50}


class AnfrageTests(unittest.TestCase):
    def test_url_nutzt_dokumentierte_parameter(self):
        url = op.anfrage_url(EAN, 30, heute=dt.date(2026, 10, 22))
        teile = urllib.parse.urlsplit(url)
        self.assertEqual((teile.scheme, teile.hostname, teile.path), ("https", "prices.openfoodfacts.org", "/api/v1/prices"))
        q = dict(urllib.parse.parse_qsl(teile.query))
        self.assertEqual(q, {"product_code": EAN, "currency": "EUR", "date__gte": "2026-09-22", "order_by": "-date",
                             "duplicate_of__isnull": "true", "size": "50", "page": "1"})

    def test_ungueltige_eingaben(self):
        for ean in ("", "123", "abc4008400402", "1" * 15):
            with self.assertRaises(ValueError):
                op.anfrage_url(ean)
        with self.assertRaises(ValueError):
            op.anfrage_url(EAN, tage=0)


class UmwandlungTests(unittest.TestCase):
    def test_gueltige_preise_mit_quelle_link_und_lizenz(self):
        zeilen, hinweise = op.zeilen_aus_antwort(antwort(
            item(11, 1.49), item(12, 0.99, price_is_discounted=True, price_without_discount=1.79)), EAN)
        self.assertEqual(hinweise, [])
        a, b = zeilen
        self.assertEqual(a["id"], "openprices-11")
        self.assertEqual(a["titel"], "Testschokolade 100 g – Testmarkt · Berlin")
        self.assertEqual(a["url"], "https://prices.openfoodfacts.org/api/v1/prices/11")
        self.assertEqual(a["referenzpreis"], "")
        self.assertEqual(b["referenzpreis"], "1.79")
        self.assertEqual(a["erfasst_am"], "2026-10-20T00:00:00+00:00")
        self.assertIn("ODbL", a["lizenz"])

    def test_unpassendes_wird_uebersprungen_und_gemeldet(self):
        zeilen, hinweise = op.zeilen_aus_antwort(antwort(
            item(1, 2.0, currency="CHF"), item(2, 2.0, product_code="123"), item(3, 2.0, price_per="KILOGRAM"),
            item(4, 2.0, duplicate_of=9), item(5, 0), item(6, "x"), item(7, 2.0, date="kaputt"), "kein objekt",
            item(8, 2.0)), EAN)
        self.assertEqual([z["id"] for z in zeilen], ["openprices-8"])
        self.assertEqual(len(hinweise), 8)

    def test_beobachtung_von_heute_liegt_nie_in_der_zukunft(self):
        kurz_nach_mitternacht = dt.datetime(2026, 10, 21, 22, 30, tzinfo=dt.timezone.utc)  # 00:30 in Berlin
        zeilen, _ = op.zeilen_aus_antwort(antwort(item(1, 1.0, datum="2026-10-22")), EAN, jetzt=kurz_nach_mitternacht)
        self.assertEqual(zeilen[0]["erfasst_am"], kurz_nach_mitternacht.isoformat())

    def test_rabatt_nur_wenn_wirklich_teurer(self):
        zeilen, _ = op.zeilen_aus_antwort(antwort(
            item(1, 2.0, price_is_discounted=True, price_without_discount=1.5)), EAN)
        self.assertEqual(zeilen[0]["referenzpreis"], "")

    def test_geaendertes_format_wird_erkannt(self):
        for kaputt in ({}, {"items": "x"}, []):
            with self.assertRaises(op.OpenPricesFehler):
                op.zeilen_aus_antwort(kaputt, EAN)


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.netz = [mock.patch("socket.create_connection", side_effect=AssertionError("Netzwerk!")),
                     mock.patch.object(socket.socket, "connect", side_effect=AssertionError("Netzwerk!"))]
        for p in self.netz:
            p.start()

    def tearDown(self):
        for p in self.netz:
            p.stop()

    def test_ohne_freigabeschalter_kein_abruf(self):
        abruf = mock.Mock()
        adapter = op.OpenPricesAdapter(EAN, abruf=abruf, umgebung={})
        with self.assertRaisesRegex(op.OpenPricesGesperrt, op.FREIGABE_VARIABLE):
            adapter.lade()
        abruf.assert_not_called()

    def test_gesperrte_quelle_bleibt_gesperrt_trotz_schalter(self):
        reg = Register([q for q in STANDARD if q.kennung != "openprices"]
                       + [Quelle("openprices", "Open Prices", AUSGESCHLOSSEN, "Test")])
        abruf = mock.Mock()
        with self.assertRaisesRegex(op.OpenPricesGesperrt, "ausgeschlossen"):
            op.OpenPricesAdapter(EAN, register=reg, abruf=abruf, umgebung=FREI).lade()
        abruf.assert_not_called()

    def test_voller_suchablauf_mit_echtem_format(self):
        heute = dt.date.today().isoformat()
        abruf = mock.Mock(return_value=antwort(
            item(21, 1.29, datum=heute), item(22, 0.89, datum=heute, price_is_discounted=True, price_without_discount=1.29),
            item(23, 1.29, currency="USD")))
        adapter = op.OpenPricesAdapter(EAN, tage=30, abruf=abruf, umgebung=FREI)
        ergebnis = finde(adapter, sortierung="preis")
        abruf.assert_called_once()
        self.assertIn(f"product_code={EAN}", abruf.call_args.args[0])
        self.assertEqual([t.angebot.id for t in ergebnis.treffer], ["openprices-22", "openprices-21"])
        self.assertEqual(ergebnis.fehler, [])
        self.assertEqual(len(adapter.hinweise), 1)
        guenstig = ergebnis.treffer[0].angebot
        self.assertEqual(str(guenstig.rabatt_prozent), "31.0")
        self.assertEqual(guenstig.quelle, "openprices")
        self.assertIn("ODbL", guenstig.extra["lizenz"])

    def test_alte_beobachtung_wird_als_veraltet_markiert(self):
        alt = (dt.date.today() - dt.timedelta(days=10)).isoformat()
        adapter = op.OpenPricesAdapter(EAN, abruf=lambda url: antwort(item(31, 1.0, datum=alt)), umgebung=FREI)
        treffer = finde(adapter).treffer
        self.assertTrue(any(w.startswith("veraltet") for w in treffer[0].warnungen))

    def test_abruf_nur_zum_erlaubten_host(self):
        for url in ("http://prices.openfoodfacts.org/api/v1/prices", "https://example.com/api/v1/prices",
                    "https://prices.openfoodfacts.org.evil.example/x"):
            with self.assertRaises(op.OpenPricesGesperrt):
                op._abruf(url)

    def test_netzfehler_wird_sauber_gemeldet(self):
        with mock.patch("urllib.request.OpenerDirector.open", side_effect=OSError("kein Netz")):
            with self.assertRaisesRegex(op.OpenPricesFehler, "nicht erreichbar"):
                op._abruf(op.anfrage_url(EAN))

    def test_user_agent_wird_gesendet(self):
        gesehen = {}

        class Antwort(io.BytesIO):
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def oeffne(opener, req, timeout=None):
            gesehen["ua"] = req.get_header("User-agent")
            return Antwort(json.dumps(antwort()).encode())

        with mock.patch("urllib.request.OpenerDirector.open", oeffne):
            self.assertEqual(op._abruf(op.anfrage_url(EAN)), antwort())
        self.assertTrue(gesehen["ua"].startswith("SCHNAPPER/"))


class KommandozeileTests(unittest.TestCase):
    def test_cli_ohne_schalter_meldet_sperre(self):
        err = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True), redirect_stderr(err):
            self.assertEqual(main(["--openprices", EAN]), 3)
        self.assertIn(op.FREIGABE_VARIABLE, err.getvalue())

    def test_cli_mit_schalter_zeigt_treffer_und_lizenz(self):
        heute = dt.date.today().isoformat()
        out = io.StringIO()
        with mock.patch.dict("os.environ", FREI), \
             mock.patch.object(op, "_abruf", return_value=antwort(item(41, 1.11, datum=heute))), redirect_stdout(out):
            self.assertEqual(main(["--openprices", EAN, "--json"]), 0)
        daten = json.loads(out.getvalue())
        self.assertEqual(daten["treffer"][0]["id"], "openprices-41")
        self.assertIn("ODbL", daten["lizenz"])

    def test_cli_datei_und_openprices_schliessen_sich_aus(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["x.csv", "--openprices", EAN])


if __name__ == "__main__":
    unittest.main()


class RegisterTests(unittest.TestCase):
    def test_standard_bleibt_spaeter(self):
        self.assertIsNotNone(Register().pruefe("openprices"))
        self.assertEqual(Register().get("openprices").entscheidung, "spaeter")

    def test_schalter_gibt_nur_diese_quelle_frei(self):
        adapter = op.OpenPricesAdapter(EAN, abruf=lambda u: antwort(), umgebung=FREI)
        self.assertIsNone(adapter.sperrgrund())
        self.assertIsNotNone(adapter._freigegebenes_register().pruefe("ebay"))
        self.assertIsNotNone(Register().pruefe("openprices"), "Standard-Register darf nicht verändert werden")
