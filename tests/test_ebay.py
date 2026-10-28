"""eBay-Adapter (S-013): ohne Netzwerk, gegen das dokumentierte Antwortformat der Browse API.

Struktur laut https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
(Stand 23.10.2026). Alle Werte sind erfunden, die Zugangsdaten sind Platzhalter.
"""
import base64
import builtins
import datetime as dt
import io
import json
import pathlib
import re
import socket
import sys
import unittest
import urllib.error
import urllib.parse
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from schnapper import ebay
from schnapper.adapter import QuelleGesperrt, finde
from schnapper.quellen import AUSGESCHLOSSEN, Quelle, Register, STANDARD

TEST_ID = "TEST-ID-xyz"
TEST_SECRET = "TEST-SECRET-xyz"
TOKEN = "TEST-TOKEN-abc"
BASIS64 = base64.b64encode(f"{TEST_ID}:{TEST_SECRET}".encode()).decode()
GEHEIM = (TEST_ID, TEST_SECRET, BASIS64, TOKEN)
JETZT = dt.datetime(2026, 10, 23, 1, 30, tzinfo=dt.timezone.utc)


def env(**mehr):
    d = {ebay.FREIGABE_VARIABLE: "ja", ebay.ID_VARIABLE: TEST_ID, ebay.SECRET_VARIABLE: TEST_SECRET}
    d.update(mehr)
    return {k: v for k, v in d.items() if v is not None}


def eintrag(item_id, preis, **mehr):
    d = {"itemId": item_id, "title": f"Testartikel {item_id}",
         "price": {"value": preis, "currency": "EUR"},
         "itemWebUrl": f"https://www.ebay.de/itm/{item_id}",
         "conditionId": "1000", "buyingOptions": ["FIXED_PRICE"],
         "categories": [{"categoryId": "1", "categoryName": "Testkategorie"}]}
    d.update(mehr)
    return d


def drei_eintraege():
    return {"total": 3, "itemSummaries": [
        eintrag("v1|111|0", "19.99", shippingOptions=[
            {"shippingCost": {"value": "4.99", "currency": "EUR"}},
            {"shippingCost": {"value": "3.50", "currency": "EUR"}},
            {"shippingCost": {"value": "1.00", "currency": "USD"}}]),
        eintrag("v1|222|0", "45.00", conditionId="3000",
                marketingPrice={"originalPrice": {"value": "60.00", "currency": "EUR"},
                                "discountPercentage": "25"}),
        eintrag("v1|333|0", "5.50", conditionId="2500", buyingOptions=["AUCTION"],
                itemWebUrl="https://www.ebay.com/itm/333"),
    ]}


class Transport:
    """Simulierter Transport: zeichnet Aufrufe auf, liefert Token und Suchantwort."""

    def __init__(self, suche=None, token=None):
        self.aufrufe = []
        self.suche = drei_eintraege() if suche is None else suche
        self.token = {"access_token": TOKEN, "expires_in": 7200, "token_type": "Application Access Token"} \
            if token is None else token

    def __call__(self, methode, url, kopf, daten):
        self.aufrufe.append((methode, url, dict(kopf), daten))
        pfad = urllib.parse.urlsplit(url).path
        if pfad == ebay.TOKEN_PFAD:
            if isinstance(self.token, Exception):
                raise self.token
            return self.token
        if isinstance(self.suche, Exception):
            raise self.suche
        return self.suche


class Antwort:
    def __init__(self, roh, status=200):
        self.roh, self.status = roh, status

    def read(self, n=-1):
        return self.roh if n < 0 else self.roh[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_fehler(url, code, body=b""):
    return urllib.error.HTTPError(url, code, "Fehler", {}, io.BytesIO(body))


class OhneNetz(unittest.TestCase):
    """Jeder echte Verbindungsversuch scheitert sofort mit AssertionError."""

    def setUp(self):
        def verboten(*a, **k):
            raise AssertionError("Netzwerkzugriff im Test")
        for ziel in (mock.patch("socket.create_connection", verboten),
                     mock.patch.object(socket.socket, "connect", verboten)):
            ziel.start()
            self.addCleanup(ziel.stop)

    def opener_verboten(self):
        return mock.patch.object(urllib.request.OpenerDirector, "open",
                                 side_effect=AssertionError("Opener darf nicht geöffnet werden"))

    def ohne_geheimnis(self, exc):
        text = str(exc) + repr(exc)
        for g in GEHEIM:
            self.assertNotIn(g, text)


class SperreTests(OhneNetz):
    def pruefe_gesperrt(self, umgebung, register=None, erwartet=None):
        t = Transport()
        a = ebay.EbayAdapter("Kopfhörer", register=register, umgebung=umgebung, transport=t)
        out, err = io.StringIO(), io.StringIO()
        with self.opener_verboten(), redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(ebay.EbayGesperrt) as cm:
                a.lade()
        self.assertIsInstance(cm.exception, QuelleGesperrt)
        self.assertEqual(t.aufrufe, [])
        self.assertEqual(out.getvalue() + err.getvalue(), "")
        self.ohne_geheimnis(cm.exception)
        if erwartet:
            self.assertIn(erwartet, str(cm.exception))
        return cm.exception

    def test_ohne_schalter_gesperrt(self):  # AK 3
        self.pruefe_gesperrt({}, erwartet=ebay.FREIGABE_VARIABLE)
        self.pruefe_gesperrt(env(**{ebay.FREIGABE_VARIABLE: "JA"}), erwartet=ebay.FREIGABE_VARIABLE)
        self.pruefe_gesperrt(env(**{ebay.FREIGABE_VARIABLE: None}), erwartet=ebay.FREIGABE_VARIABLE)

    def test_fehlende_schluessel(self):  # AK 4
        for name in (ebay.ID_VARIABLE, ebay.SECRET_VARIABLE):
            for wert in (None, "", "   "):
                with self.subTest(name=name, wert=wert):
                    exc = self.pruefe_gesperrt(env(**{name: wert}), erwartet=name)
                    andere = ebay.SECRET_VARIABLE if name == ebay.ID_VARIABLE else ebay.ID_VARIABLE
                    self.assertNotIn(andere, str(exc))

    def test_ausgeschlossen_bleibt_gesperrt(self):  # AK 5
        reg = Register([q for q in STANDARD if q.kennung != "ebay"]
                       + [Quelle("ebay", "eBay", AUSGESCHLOSSEN, "Test")])
        self.pruefe_gesperrt(env(), register=reg, erwartet="ausgeschlossen")
        reg_ohne = Register([q for q in STANDARD if q.kennung != "ebay"])
        self.pruefe_gesperrt(env(), register=reg_ohne, erwartet="nicht freigegeben")

    def test_standardregister_bleibt_unveraendert(self):  # AK 5
        a = ebay.EbayAdapter("Kopfhörer", umgebung=env(), transport=Transport(), jetzt=JETZT)
        self.assertIsNone(a.sperrgrund())
        a.lade()
        self.assertIsNotNone(Register().pruefe("ebay"))
        self.assertIn("noch gesperrt", a.register.pruefe("ebay"))

    def test_umgebung_standard_ist_os_environ(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            a = ebay.EbayAdapter("x")
            self.assertIn(ebay.FREIGABE_VARIABLE, a.sperrgrund())


class EingabeTests(OhneNetz):
    def test_ungueltige_eingaben(self):  # AK 18
        for begriff in ("", "   ", "x" * 101, None):
            with self.assertRaises(ValueError):
                ebay.EbayAdapter(begriff, umgebung={})
        for limit in (0, 51, -1, True, "10"):
            with self.assertRaises(ValueError):
                ebay.EbayAdapter("Kopfhörer", umgebung={}, limit=limit)
        self.assertEqual(ebay.EbayAdapter("  " + "x" * 100 + " ", umgebung={}).suchbegriff, "x" * 100)


class UmgebungTests(OhneNetz):
    def hosts(self, umgebung):
        t = Transport()
        ebay.EbayAdapter("Kopfhörer", umgebung=umgebung, transport=t, jetzt=JETZT).lade()
        return {urllib.parse.urlsplit(u).hostname for _, u, _, _ in t.aufrufe}

    def test_sandbox_standard(self):  # AK 6
        for wert in (None, "nein", "JA", "1", " ja", ""):
            with self.subTest(wert=wert):
                self.assertEqual(self.hosts(env(**{ebay.PRODUKTION_VARIABLE: wert})), {ebay.SANDBOX_HOST})

    def test_produktion_nur_mit_ja(self):  # AK 7
        self.assertEqual(self.hosts(env(**{ebay.PRODUKTION_VARIABLE: "ja"})), {ebay.PRODUKTION_HOST})
        a = ebay.EbayAdapter("x", umgebung=env(**{ebay.PRODUKTION_VARIABLE: "ja"}))
        self.assertEqual(a.umgebung_name(), "produktion")
        self.assertEqual(a.host(), "api.ebay.com")


class OAuthTests(OhneNetz):
    def test_token_und_suche(self):  # AK 12
        t = Transport()
        ebay.EbayAdapter("Kopfhörer Bluetooth", umgebung=env(), transport=t, jetzt=JETZT, limit=20).lade()
        self.assertEqual(len(t.aufrufe), 2)
        (m1, u1, k1, d1), (m2, u2, k2, d2) = t.aufrufe
        self.assertEqual(m1, "POST")
        self.assertEqual(u1, "https://api.sandbox.ebay.com/identity/v1/oauth2/token")
        self.assertEqual(k1["Authorization"], "Basic " + BASIS64)
        self.assertEqual(k1["Content-Type"], "application/x-www-form-urlencoded")
        body = urllib.parse.parse_qs(d1.decode())
        self.assertEqual(body, {"grant_type": ["client_credentials"],
                                "scope": ["https://api.ebay.com/oauth/api_scope"]})
        self.assertEqual(m2, "GET")
        teile = urllib.parse.urlsplit(u2)
        self.assertEqual((teile.scheme, teile.hostname, teile.path),
                         ("https", "api.sandbox.ebay.com", "/buy/browse/v1/item_summary/search"))
        q = urllib.parse.parse_qs(teile.query)
        self.assertEqual(q["q"], ["Kopfhörer Bluetooth"])
        self.assertEqual(q["limit"], ["20"])
        self.assertLessEqual(int(q["limit"][0]), 50)
        self.assertEqual(q["filter"], ["deliveryCountry:DE,priceCurrency:EUR"])
        self.assertEqual(k2["Authorization"], "Bearer " + TOKEN)
        self.assertEqual(k2["X-EBAY-C-MARKETPLACE-ID"], "EBAY_DE")
        self.assertEqual(k2["Accept"], "application/json")
        self.assertEqual(k2["Accept-Language"], "de-DE")
        self.assertIsNone(d2)
        for _, url, _, _ in t.aufrufe:
            for g in GEHEIM:
                self.assertNotIn(g, url)

    def test_token_cache_nur_im_speicher(self):  # AK 17
        t = Transport()
        a = ebay.EbayAdapter("Kopfhörer", umgebung=env(), transport=t, jetzt=JETZT)
        with mock.patch.object(builtins, "open", side_effect=AssertionError("Datei geschrieben")):
            a.lade()
            a.lade()
        self.assertEqual([m for m, *_ in t.aufrufe], ["POST", "GET", "GET"])
        self.assertNotIn(TOKEN, repr(a))

    def test_token_abgelaufen(self):
        t = Transport(token={"access_token": TOKEN, "expires_in": 30})
        a = ebay.EbayAdapter("Kopfhörer", umgebung=env(), transport=t, jetzt=JETZT)
        a.lade()
        a.lade()
        self.assertEqual([m for m, *_ in t.aufrufe], ["POST", "GET", "POST", "GET"])

    def test_token_antwort_unbrauchbar(self):  # AK 15
        for token in ({}, {"access_token": "", "expires_in": 7200}, {"access_token": TOKEN},
                      {"access_token": TOKEN, "expires_in": 0}, {"access_token": TOKEN, "expires_in": True},
                      {"access_token": 5, "expires_in": 7200}, []):
            with self.subTest(token=token):
                t = Transport(token=token)
                with self.assertRaises(ebay.EbayFehler) as cm:
                    ebay.EbayAdapter("x", umgebung=env(), transport=t).lade()
                self.assertIn("Token-Antwort unbrauchbar", str(cm.exception))
                self.ohne_geheimnis(cm.exception)
                self.assertEqual(len(t.aufrufe), 1)


class AbbildungTests(OhneNetz):
    def test_drei_eintraege(self):  # AK 13
        a = ebay.EbayAdapter("Kopfhörer", umgebung=env(), transport=Transport(), jetzt=JETZT)
        erg = a.lade()
        self.assertEqual(erg.fehler, [])
        self.assertEqual(a.hinweise, [])
        nach_id = {x.id: x for x in erg.angebote}
        self.assertEqual(set(nach_id), {"ebay-v1|111|0", "ebay-v1|222|0", "ebay-v1|333|0"})
        neu, gebraucht, auktion = nach_id["ebay-v1|111|0"], nach_id["ebay-v1|222|0"], nach_id["ebay-v1|333|0"]
        for x in erg.angebote:
            self.assertEqual(x.quelle, "ebay")
            self.assertTrue(x.titel.startswith("SANDBOX "))
            teile = urllib.parse.urlsplit(x.url)
            self.assertEqual(teile.scheme, "https")
            self.assertRegex(teile.hostname, r"(^|\.)ebay\.(de|com)$")
            self.assertEqual(x.extra["umgebung"], "sandbox")
            self.assertEqual(x.extra["hinweis_quelle"], "Daten: eBay Browse API")
            self.assertEqual(x.erfasst_am, JETZT)
        self.assertEqual(str(neu.preis), "19.99")
        self.assertEqual(str(neu.versand), "3.50")
        self.assertEqual(neu.zustand, "neu")
        self.assertIsNone(neu.referenzpreis)
        self.assertNotIn("versand_unbekannt", neu.extra)
        self.assertEqual(neu.kategorie, "Testkategorie")
        self.assertEqual(gebraucht.zustand, "gebraucht")
        self.assertEqual(str(gebraucht.referenzpreis), "60.00")
        self.assertEqual(gebraucht.versand, 0)
        self.assertTrue(gebraucht.extra["versand_unbekannt"])
        self.assertEqual(auktion.zustand, "wie_neu")
        self.assertEqual(auktion.extra["kaufoptionen"], ["AUCTION"])
        ergebnis = finde(ebay.EbayAdapter("Kopfhörer", umgebung=env(), transport=Transport(), jetzt=JETZT),
                         jetzt=JETZT)
        self.assertEqual(ergebnis.fehler, [])
        self.assertGreaterEqual(len(ergebnis.treffer), 1)

    def test_produktion_ohne_sandbox_praefix(self):
        zeilen, _ = ebay.zeilen_aus_antwort(drei_eintraege(), "produktion", JETZT)
        self.assertTrue(all(not z["titel"].startswith("SANDBOX") for z in zeilen))
        self.assertTrue(all(z["umgebung"] == "produktion" for z in zeilen))

    def test_referenzpreis_nur_wenn_hoeher(self):
        z, _ = ebay.zeilen_aus_antwort({"itemSummaries": [eintrag("a", "50", marketingPrice={
            "originalPrice": {"value": "40", "currency": "EUR"}})]}, jetzt=JETZT)
        self.assertEqual(z[0]["referenzpreis"], "")

    def test_zustaende(self):
        erwartet = {"1000": "neu", "1500": "wie_neu", "2000": "wie_neu", "2990": "wie_neu",
                    "3000": "gebraucht", "6000": "gebraucht", "7000": "defekt",
                    "9999": "unbekannt", None: "unbekannt", "abc": "unbekannt", True: "unbekannt"}
        for cid, z in erwartet.items():
            self.assertEqual(ebay.zustand_aus_condition_id(cid), z, cid)

    def test_unbrauchbare_eintraege(self):  # AK 14
        antwort = {"itemSummaries": [
            eintrag("usd", "10", price={"value": "10", "currency": "USD"}),
            eintrag("ohnepreis", None, price=None),
            eintrag("nan", "NaN"),
            eintrag("bool", True),
            eintrag("neg", "-5"),
            {k: v for k, v in eintrag("x", "10").items() if k != "itemId"},
            eintrag("", "10"),
            eintrag("fremd", "10", itemWebUrl="https://evil.example/itm/1"),
            eintrag("fake", "10", itemWebUrl="https://ebay.de.evil.example/itm/1"),
            eintrag("http", "10", itemWebUrl="http://www.ebay.de/itm/1"),
            "kein objekt",
            eintrag("gut", "10"),
        ]}
        a = ebay.EbayAdapter("x", umgebung=env(), transport=Transport(suche=antwort), jetzt=JETZT)
        erg = a.lade()
        self.assertEqual([x.id for x in erg.angebote], ["ebay-gut"])
        self.assertEqual(erg.fehler, [])
        self.assertEqual(len(a.hinweise), 11)
        self.assertTrue(any("USD" in h for h in a.hinweise))

    def test_mehr_als_50(self):  # AK 14
        antwort = {"itemSummaries": [eintrag(f"i{n}", "10") for n in range(60)]}
        zeilen, hinweise = ebay.zeilen_aus_antwort(antwort, jetzt=JETZT)
        self.assertEqual(len(zeilen), 50)
        self.assertTrue(any("50" in h for h in hinweise))

    def test_ohne_item_summaries(self):  # AK 14
        a = ebay.EbayAdapter("x", umgebung=env(), transport=Transport(suche={"total": 0}), jetzt=JETZT)
        erg = a.lade()
        self.assertEqual((erg.angebote, erg.fehler), ([], []))

    def test_kaputte_struktur(self):
        for antwort in ([], "x", {"itemSummaries": "x"}, {"itemSummaries": {}}):
            with self.assertRaises(ebay.EbayFehler):
                ebay.zeilen_aus_antwort(antwort, jetzt=JETZT)


class AnfrageTests(OhneNetz):
    GUT = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search?q=x"
    KOPF = {"Authorization": "Basic " + BASIS64}

    def anfrage(self, *, antwort=None, fehler=None, url=GUT, methode="GET", **k):
        opener = mock.Mock()
        if fehler is not None:
            opener.open.side_effect = fehler
        else:
            opener.open.return_value = antwort
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ebay, "_oeffner", return_value=opener), redirect_stdout(out), redirect_stderr(err):
            try:
                return ebay._anfrage(methode, url, self.KOPF, None, **k), opener
            finally:
                self.assertEqual(out.getvalue() + err.getvalue(), "")

    def fehler(self, art=ebay.EbayFehler, **k):
        with self.assertRaises(art) as cm:
            self.anfrage(**k)
        self.assertNotIsInstance(cm.exception, (AssertionError, TypeError, KeyError))
        self.ohne_geheimnis(cm.exception)
        return str(cm.exception)

    def test_host_allowlist(self):  # AK 8
        schlecht = [
            ("GET", "http://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"),
            ("GET", "https://api.ebay.com.evil.example/buy/browse/v1/item_summary/search"),
            ("POST", "https://evil.example/identity/v1/oauth2/token"),
            ("GET", "https://www.ebay.com/buy/browse/v1/item_summary/search"),
            ("GET", "https://u:p@api.ebay.com/buy/browse/v1/item_summary/search"),
            ("GET", "https://api.ebay.com:8443/buy/browse/v1/item_summary/search"),
            ("GET", "https://api.ebay.com:99999/buy/browse/v1/item_summary/search"),
            ("GET", "https://api.ebay.com:abc/buy/browse/v1/item_summary/search"),
            ("GET", "https://api.ebay.com/buy/browse/v1/item/123"),
            ("DELETE", "https://api.ebay.com/buy/browse/v1/item_summary/search"),
        ]
        with mock.patch.object(ebay, "_oeffner", side_effect=AssertionError("Opener gebaut")), self.opener_verboten():
            for methode, url in schlecht:
                with self.subTest(url=url, methode=methode):
                    with self.assertRaises(ebay.EbayGesperrt) as cm:
                        ebay._anfrage(methode, url, self.KOPF, None)
                    self.ohne_geheimnis(cm.exception)
        self.assertEqual(ebay.ERLAUBTE_HOSTS, frozenset({"api.ebay.com", "api.sandbox.ebay.com"}))

    def test_kaputte_url_gesperrt(self):  # S-013: ValueError aus urlsplit wird EbayGesperrt
        kaputt = [
            ("POST", "https://[::1/identity/v1/oauth2/token"),
            ("GET", "https://api.ebay.com]/buy/browse/v1/item_summary/search"),
            ("POST", "https://api.ebay.com＃@evil.example/identity/v1/oauth2/token"),
        ]
        with mock.patch.object(ebay, "_oeffner", side_effect=AssertionError("Opener gebaut")), self.opener_verboten():
            for methode, url in kaputt:
                with self.subTest(url=url, methode=methode):
                    with self.assertRaises(ebay.EbayGesperrt) as cm:
                        ebay._anfrage(methode, url, self.KOPF, None)
                    self.assertIsNone(cm.exception.__cause__)
                    self.assertTrue(cm.exception.__suppress_context__)
                    self.ohne_geheimnis(cm.exception)
                    self.assertNotIn("evil", str(cm.exception))
                    self.assertNotIn(url, str(cm.exception))

    def test_erlaubt_mit_port_443_und_timeout(self):  # AK 10
        daten, opener = self.anfrage(antwort=Antwort(b'{"ok": 1}'))
        self.assertEqual(daten, {"ok": 1})
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 15.0)
        _, opener = self.anfrage(antwort=Antwort(b"{}"), timeout=3.0,
                                 url="https://api.ebay.com:443/identity/v1/oauth2/token", methode="POST")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 3.0)
        req = opener.open.call_args.args[0]
        self.assertEqual(req.get_method(), "POST")

    def test_keine_weiterleitung(self):  # AK 9
        opener = ebay._oeffner()
        handler = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
        self.assertTrue(handler)
        self.assertTrue(all(isinstance(h, ebay._KeineWeiterleitung) for h in handler))
        self.assertIsNone(handler[0].redirect_request(None, None, 302, "Found", {}, "https://evil.example/"))
        _, op = None, None
        with self.assertRaises(ebay.EbayFehler) as cm:
            _, op = self.anfrage(fehler=http_fehler(self.GUT, 302))
        self.assertIn("302", str(cm.exception))

    def test_302_kein_zweiter_request(self):  # AK 9
        opener = mock.Mock()
        opener.open.side_effect = http_fehler(self.GUT, 302)
        with mock.patch.object(ebay, "_oeffner", return_value=opener):
            with self.assertRaises(ebay.EbayFehler):
                ebay._anfrage("GET", self.GUT, {}, None)
        self.assertEqual(opener.open.call_count, 1)

    def test_timeout_und_oserror(self):  # AK 10
        self.assertIn("nicht erreichbar", self.fehler(fehler=socket.timeout("timed out")))
        self.assertIn("nicht erreichbar", self.fehler(fehler=urllib.error.URLError("Name or service not known")))
        self.assertIn("nicht erreichbar", self.fehler(fehler=ConnectionResetError()))

    def test_groessenlimit_und_json(self):  # AK 11
        self.assertIn("zu groß", self.fehler(antwort=Antwort(b"x" * 2_000_001)))
        self.assertIn("JSON", self.fehler(antwort=Antwort(b"{kaputt")))
        self.assertIn("UTF-8", self.fehler(antwort=Antwort(b'{"a": "\xff"}')))
        daten, _ = self.anfrage(antwort=Antwort(b'{"a": "' + b"y" * 1_999_990 + b'"}'))
        self.assertIn("a", daten)

    def test_json_zu_tief_oder_zu_lange_zahl(self):  # AK 11 (S-013 Nachtrag)
        for koerper in (b"[" * 100_000, b"1" * 5000):
            with self.subTest(laenge=len(koerper), anfang=koerper[:1]):
                opener = mock.Mock()
                opener.open.return_value = Antwort(koerper)
                with mock.patch.object(ebay, "_oeffner", return_value=opener):
                    with self.assertRaises(ebay.EbayFehler) as cm:
                        ebay._anfrage("GET", self.GUT, {}, None)
                self.assertNotIsInstance(cm.exception, (RecursionError, AssertionError))
                self.assertEqual(str(cm.exception), "eBay-Antwort ist kein gültiges JSON/UTF-8")
                self.assertIsNone(cm.exception.__cause__)
                self.assertTrue(cm.exception.__suppress_context__)
                self.ohne_geheimnis(cm.exception)
                self.assertIn("JSON", self.fehler(antwort=Antwort(koerper)))

    def test_status_nicht_200(self):
        self.assertIn("204", self.fehler(antwort=Antwort(b"{}", status=204)))

    def test_http_fehler_token_401(self):  # AK 15
        body = json.dumps({"errors": [{"errorId": 1003, "message": "Ungültig " + "z" * 500}]}).encode()
        text = self.fehler(fehler=http_fehler("https://api.sandbox.ebay.com/identity/v1/oauth2/token", 401, body),
                           url="https://api.sandbox.ebay.com/identity/v1/oauth2/token", methode="POST")
        self.assertIn("eBay HTTP 401", text)
        self.assertIn("1003", text)
        self.assertIn("Zugangsdaten ungültig oder falscher Modus (Sandbox/Produktion)?", text)
        self.assertLess(text.count("z"), 201)

    def test_http_fehler_suche_500(self):  # AK 15
        text = self.fehler(fehler=http_fehler(self.GUT, 500, b"kein json"))
        self.assertTrue(text.startswith("eBay HTTP 500"))
        self.assertNotIn("Zugangsdaten", text)

    def test_adapter_fehler_ohne_geheimnisse(self):  # AK 15/16
        faelle = [Transport(token=ebay.EbayFehler("eBay HTTP 401")),
                  Transport(token={"expires_in": 7200}),
                  Transport(suche=ebay.EbayFehler("eBay HTTP 500"))]
        for t in faelle:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err), self.assertRaises(ebay.EbayFehler) as cm:
                ebay.EbayAdapter("x", umgebung=env(), transport=t, jetzt=JETZT).lade()
            self.ohne_geheimnis(cm.exception)
            self.assertEqual(out.getvalue() + err.getvalue(), "")

    def test_ende_zu_ende_mit_simuliertem_opener(self):  # AK 12/15 über den echten _anfrage-Pfad
        antworten = [Antwort(json.dumps({"access_token": TOKEN, "expires_in": 7200}).encode()),
                     http_fehler(self.GUT, 500, b"{}")]
        opener = mock.Mock()
        opener.open.side_effect = antworten
        with mock.patch.object(ebay, "_oeffner", return_value=opener):
            with self.assertRaises(ebay.EbayFehler) as cm:
                ebay.EbayAdapter("x", umgebung=env(), jetzt=JETZT).lade()
        self.ohne_geheimnis(cm.exception)
        token_req = opener.open.call_args_list[0].args[0]
        self.assertEqual(token_req.get_method(), "POST")
        self.assertEqual(token_req.full_url, "https://api.sandbox.ebay.com/identity/v1/oauth2/token")


class QuelltextTests(unittest.TestCase):
    QUELLE = (ROOT / "app" / "schnapper" / "ebay.py").read_text(encoding="utf-8")

    def test_nur_standardbibliothek_kein_print_logging(self):  # AK 2/16
        importe = re.findall(r"^(?:from|import)\s+([\w.]+)", self.QUELLE, re.M)
        erlaubt = {"__future__", "base64", "datetime", "json", "os", "re", "time", "urllib.error",
                   "urllib.parse", "urllib.request", "decimal", ".adapter", ".einlesen", ".quellen"}
        self.assertTrue(set(importe) <= erlaubt, set(importe) - erlaubt)
        treffer = re.search(r"\bprint\(|\blogging\b|(?<![.\w])open\(|write_text|write_bytes", self.QUELLE)
        self.assertIsNone(treffer, treffer and treffer.group(0))
        self.assertNotIn("openprices", self.QUELLE)

    def test_freigabe_variable_wie_platzhalter(self):
        from schnapper import adapter
        self.assertEqual(ebay.FREIGABE_VARIABLE, adapter.EbayAdapter.FREIGABE_VARIABLE)


class DokuTests(unittest.TestCase):  # AK 21
    def test_doku(self):
        pfad = ROOT / "docs" / "EBAY.md"
        self.assertTrue(pfad.is_file())
        text = pfad.read_text(encoding="utf-8")
        for wort in (ebay.FREIGABE_VARIABLE, ebay.PRODUKTION_VARIABLE, ebay.ID_VARIABLE, ebay.SECRET_VARIABLE,
                     "Sandbox", "Genehmigung", "developer.ebay.com",
                     "Quelle bleibt gesperrt, solange Schalter oder Schlüssel fehlen"):
            self.assertIn(wort, text)
        self.assertIsNone(re.search(r"(SBX|PRD)-[0-9a-fA-F]{6,}", text))
        self.assertIsNone(re.search(r"CLIENT_(ID|SECRET)=(?!<)\S", text))
        self.assertIsNone(re.search(r"sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY", text))


if __name__ == "__main__":
    unittest.main()
