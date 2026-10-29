"""eBay-Adapter (Quelle Q1, Aufgabe S-013): eBay Browse API, vorbereitet und gesperrt.

Standard ist die eBay-Sandbox (Testdaten). Die Produktion nutzt der Adapter nur mit
SCHNAPPER_EBAY_PRODUKTION=ja. Die Produktivnutzung der Buy/Browse API braucht
außerdem eine Genehmigung von eBay.
Netzwerk gibt es nur mit SCHNAPPER_EBAY_FREIGABE=ja (Entscheidung von Jefrey) und mit
Zugangsdaten in SCHNAPPER_EBAY_CLIENT_ID / SCHNAPPER_EBAY_CLIENT_SECRET.
Zugangsdaten und Token stehen nur im Arbeitsspeicher und erscheinen nie in Meldungen.
Erlaubt sind nur api.ebay.com und api.sandbox.ebay.com, nur HTTPS, keine Weiterleitungen.

Kosten: 0 €. Belege (Stand 23.10.2026):
  https://developer.ebay.com/api-docs/buy/browse/overview.html
  https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

from .adapter import QuelleGesperrt
from .einlesen import Importergebnis, lies_text
from .quellen import AUSGESCHLOSSEN, ERLAUBT, SPAETER, Quelle, Register

SANDBOX_HOST = "api.sandbox.ebay.com"
PRODUKTION_HOST = "api.ebay.com"
ERLAUBTE_HOSTS = frozenset({SANDBOX_HOST, PRODUKTION_HOST})
TOKEN_PFAD = "/identity/v1/oauth2/token"
SUCH_PFAD = "/buy/browse/v1/item_summary/search"
ERLAUBTE_PFADE = frozenset({TOKEN_PFAD, SUCH_PFAD})
# Scope-Bezeichner (gilt für Sandbox und Produktion) – kein Ziel-Host.
SCOPE = "https://api.ebay.com/oauth/api_scope"
MARKTPLATZ = "EBAY_DE"
MAX_ERGEBNISSE = 50
MAX_ANTWORT_BYTES = 2_000_000
MAX_FEHLER_BYTES = 64 * 1024
TIMEOUT = 15.0
MAX_SUCHBEGRIFF = 100
MAX_ID = 120

FREIGABE_VARIABLE = "SCHNAPPER_EBAY_FREIGABE"
PRODUKTION_VARIABLE = "SCHNAPPER_EBAY_PRODUKTION"
ID_VARIABLE = "SCHNAPPER_EBAY_CLIENT_ID"
SECRET_VARIABLE = "SCHNAPPER_EBAY_CLIENT_SECRET"

HINWEIS_QUELLE = "Daten: eBay Browse API"
EBAY_WEB_HOSTS = ("ebay.de", "ebay.com")


class EbayGesperrt(QuelleGesperrt):
    """Abruf nicht erlaubt (Schalter, Zugangsdaten, Register oder Ziel-URL)."""


class EbayFehler(RuntimeError):
    """Antwort unbrauchbar oder eBay nicht erreichbar."""


def _preis(wert) -> Decimal | None:
    """Keine NaN/Infinity, Bool-Werte oder Beträge außerhalb der Angebotsgrenzen."""
    if isinstance(wert, bool) or wert is None:
        return None
    try:
        d = Decimal(str(wert))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return d if d.is_finite() and Decimal("0.005") <= d <= Decimal("1000000") else None


def _versandkosten(wert) -> Decimal | None:
    """Versand darf 0 sein, sonst wie _preis."""
    if isinstance(wert, bool) or wert is None:
        return None
    try:
        d = Decimal(str(wert))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return d if d.is_finite() and Decimal("0") <= d <= Decimal("1000000") else None


def _betrag_eur(objekt, pruefer=_preis) -> Decimal | None:
    if not isinstance(objekt, dict) or objekt.get("currency") != "EUR":
        return None
    return pruefer(objekt.get("value"))


def zustand_aus_condition_id(condition_id) -> str:
    if isinstance(condition_id, bool):
        return "unbekannt"
    try:
        c = int(str(condition_id).strip())
    except (TypeError, ValueError):
        return "unbekannt"
    if c == 1000:
        return "neu"
    if c == 1500 or 2000 <= c <= 2990:
        return "wie_neu"
    if 3000 <= c <= 6000:
        return "gebraucht"
    if c == 7000:
        return "defekt"
    return "unbekannt"


def _ebay_web_url(url) -> bool:
    if not isinstance(url, str):
        return False
    try:
        teile = urllib.parse.urlsplit(url)
        port_ok = teile.port in (None, 443)
    except ValueError:
        return False
    host = (teile.hostname or "").lower()
    if teile.scheme != "https" or not port_ok or teile.username is not None or teile.password is not None:
        return False
    return host in EBAY_WEB_HOSTS or any(host.endswith("." + h) for h in EBAY_WEB_HOSTS)


def zeilen_aus_antwort(antwort, umgebung: str = "sandbox",
                       jetzt: dt.datetime | None = None) -> tuple[list[dict], list[str]]:
    """Bildet eine Browse-Antwort (item_summary/search) auf SCHNAPPER-Rohzeilen ab.

    Unbrauchbare Einträge werden übersprungen und in den Hinweisen gemeldet.
    """
    if not isinstance(antwort, dict):
        raise EbayFehler("Antwort ist kein JSON-Objekt – Format hat sich geändert?")
    items = antwort.get("itemSummaries")
    if items is None:
        # Browse may omit itemSummaries for a genuine zero-result search.
        # A missing list with positive/unknown total must not look like a
        # successful empty search (e.g. upstream response format changed).
        if type(antwort.get("total")) is not int or antwort["total"] != 0:
            raise EbayFehler("'itemSummaries' fehlt bei unbekannter oder positiver Trefferzahl")
        items = []
    if not isinstance(items, list):
        raise EbayFehler("'itemSummaries' ist keine Liste – Format hat sich geändert?")
    jetzt = jetzt or dt.datetime.now(dt.timezone.utc)
    if jetzt.tzinfo is None:
        raise ValueError("Prüfzeitpunkt muss eine Zeitzone enthalten")
    erfasst = jetzt.astimezone(dt.timezone.utc).isoformat()
    umgebung = "produktion" if umgebung == "produktion" else "sandbox"
    zeilen, hinweise = [], []
    if len(items) > MAX_ERGEBNISSE:
        hinweise.append(f"Antwort enthält mehr als {MAX_ERGEBNISSE} Angebote – nur die ersten werden verarbeitet")
    for nr, item in enumerate(items[:MAX_ERGEBNISSE], start=1):
        if not isinstance(item, dict):
            hinweise.append(f"Eintrag {nr}: ohne Objektstruktur – übersprungen")
            continue
        item_id = item.get("itemId")
        if not isinstance(item_id, str) or not item_id.strip():
            hinweise.append(f"Eintrag {nr}: ohne itemId – übersprungen")
            continue
        kennung = f"Angebot {item_id.strip()[:60]}"
        titel = item.get("title")
        if not isinstance(titel, str) or not titel.strip():
            hinweise.append(f"{kennung}: ohne Titel – übersprungen")
            continue
        preis_obj = item.get("price")
        waehrung = preis_obj.get("currency") if isinstance(preis_obj, dict) else None
        if waehrung != "EUR":
            hinweise.append(f"{kennung}: Währung {str(waehrung)[:10]} statt EUR – übersprungen")
            continue
        preis = _preis(preis_obj.get("value"))
        if preis is None:
            hinweise.append(f"{kennung}: ohne gültigen Preis – übersprungen")
            continue
        url = item.get("itemWebUrl")
        if not _ebay_web_url(url):
            hinweise.append(f"{kennung}: Link nicht https auf einem eBay-Host – übersprungen")
            continue
        versand_werte = []
        optionen = item.get("shippingOptions")
        if isinstance(optionen, list):
            for opt in optionen:
                if isinstance(opt, dict):
                    v = _betrag_eur(opt.get("shippingCost"), _versandkosten)
                    if v is not None:
                        versand_werte.append(v)
        marketing = item.get("marketingPrice")
        original = _betrag_eur(marketing.get("originalPrice")) if isinstance(marketing, dict) else None
        titel = titel.strip()
        if umgebung == "sandbox":
            titel = "SANDBOX " + titel
        zeile = {
            "id": ("ebay-" + item_id.strip())[:MAX_ID],
            "titel": titel[:300],
            "preis": str(preis),
            "waehrung": "EUR",
            "versand": str(min(versand_werte)) if versand_werte else "0",
            "referenzpreis": str(original) if original is not None and original > preis else "",
            "url": url,
            "quelle": "ebay",
            "erfasst_am": erfasst,
            "zustand": zustand_aus_condition_id(item.get("conditionId")),
            "kaufoptionen": [x for x in item.get("buyingOptions", []) if isinstance(x, str)]
            if isinstance(item.get("buyingOptions"), list) else [],
            "umgebung": umgebung,
            "hinweis_quelle": HINWEIS_QUELLE,
        }
        if not versand_werte:
            zeile["versand_unbekannt"] = True
        kategorien = item.get("categories")
        if isinstance(kategorien, list) and kategorien and isinstance(kategorien[0], dict) \
                and isinstance(kategorien[0].get("categoryName"), str):
            zeile["kategorie"] = kategorien[0]["categoryName"].strip()[:100]
        zeilen.append(zeile)
    return zeilen, hinweise


class _KeineWeiterleitung(urllib.request.HTTPRedirectHandler):
    """3xx wird nie verfolgt, sondern endet als HTTPError."""

    def redirect_request(self, *a, **k):
        return None


def _oeffner() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_KeineWeiterleitung)


def _fehlertext(exc: urllib.error.HTTPError) -> str:
    detail = ""
    try:
        roh = exc.read(MAX_FEHLER_BYTES) if exc.fp is not None else b""
        daten = json.loads(roh)
        fehler = daten.get("errors") if isinstance(daten, dict) else None
        if isinstance(fehler, list) and fehler and isinstance(fehler[0], dict):
            teile = []
            if fehler[0].get("errorId") is not None:
                teile.append(f"errorId {str(fehler[0]['errorId'])[:20]}")
            if isinstance(fehler[0].get("message"), str):
                teile.append(fehler[0]["message"])
            detail = " – ".join(teile)
    except Exception:  # Fehlertext ist nur Zusatzinfo
        detail = ""
    return " ".join(detail.split())[:200]


def _anfrage(methode: str, url: str, kopfzeilen: dict, daten: bytes | None = None,
             timeout: float = TIMEOUT) -> dict:
    """Einzige Stelle mit Netzzugriff. Prüft Ziel, blockiert Weiterleitungen, begrenzt Größe."""
    if methode not in ("GET", "POST"):
        raise EbayGesperrt("Nur GET und POST sind erlaubt")
    try:
        teile = urllib.parse.urlsplit(url)
    except ValueError:  # syntaktisch kaputte URL: wie unerlaubtes Ziel, ohne URL im Kontext
        raise EbayGesperrt("Nur Token- und Suchendpunkt auf https://api.ebay.com bzw. "
                           "https://api.sandbox.ebay.com sind erlaubt") from None
    try:
        port_erlaubt = teile.port in (None, 443)
    except ValueError:
        port_erlaubt = False
    if (teile.scheme != "https" or teile.hostname not in ERLAUBTE_HOSTS
            or teile.username is not None or teile.password is not None
            or not port_erlaubt or teile.path not in ERLAUBTE_PFADE):
        raise EbayGesperrt("Nur Token- und Suchendpunkt auf https://api.ebay.com bzw. "
                           "https://api.sandbox.ebay.com sind erlaubt")
    req = urllib.request.Request(url, data=daten, headers=dict(kopfzeilen), method=methode)
    # `timeout` gilt bei urllib nur pro Socket-Operation. Die Frist begrenzt die ganze Anfrage:
    # read1() blockiert höchstens einen Socket-Timeout, also dauert es im schlimmsten Fall
    # `timeout` + 1 Socket-Timeout, bis die Schleife abbricht.
    frist = time.monotonic() + timeout
    zu_langsam = False
    try:
        with _oeffner().open(req, timeout=timeout) as antwort:
            if antwort.status != 200:
                raise EbayFehler(f"eBay HTTP {antwort.status}")
            stuecke: list[bytes] = []
            gelesen = 0
            while gelesen <= MAX_ANTWORT_BYTES:
                stueck = antwort.read1(min(64 * 1024, MAX_ANTWORT_BYTES + 1 - gelesen))
                if not stueck:
                    break
                stuecke.append(stueck)
                gelesen += len(stueck)
                if time.monotonic() > frist:
                    zu_langsam = True
                    break
            roh = b"".join(stuecke)
    except urllib.error.HTTPError as exc:
        meldung = f"eBay HTTP {exc.code}"
        detail = _fehlertext(exc)
        if detail:
            meldung += f": {detail}"
        if exc.code in (401, 403) and teile.path == TOKEN_PFAD:
            meldung += " – Zugangsdaten ungültig oder falscher Modus (Sandbox/Produktion)?"
        raise EbayFehler(meldung) from None
    except ValueError:  # z. B. ungültiger Kopfzeilenwert – Text enthielte den Wert
        raise EbayFehler("Anfrage an eBay ungültig (Kopfzeile)") from None
    except OSError as exc:  # URLError, Timeout, Verbindungsfehler
        grund = getattr(exc, "reason", None) or exc.__class__.__name__
        raise EbayFehler(f"eBay nicht erreichbar: {str(grund)[:200]}") from None
    if zu_langsam:
        raise EbayFehler(f"eBay antwortet zu langsam (Zeitlimit {timeout:g} s überschritten)")
    if len(roh) > MAX_ANTWORT_BYTES:
        raise EbayFehler("eBay-Antwort zu groß")
    try:
        return json.loads(roh.decode("utf-8"))
    except (ValueError, RecursionError):  # inkl. JSONDecodeError, UnicodeDecodeError, zu tief, zu lange Zahl
        raise EbayFehler("eBay-Antwort ist kein gültiges JSON/UTF-8") from None


class EbayAdapter:
    """Angebote aus der eBay Browse API. `transport` ist austauschbar (Tests ohne Netz)."""

    kennung = "ebay"

    def __init__(self, suchbegriff: str, register: Register | None = None, umgebung=None,
                 transport=None, jetzt: dt.datetime | None = None, limit: int = MAX_ERGEBNISSE):
        suchbegriff = (suchbegriff or "").strip() if isinstance(suchbegriff, str) else ""
        if not 1 <= len(suchbegriff) <= MAX_SUCHBEGRIFF:
            raise ValueError(f"Suchbegriff muss 1 bis {MAX_SUCHBEGRIFF} Zeichen lang sein")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ERGEBNISSE:
            raise ValueError(f"limit muss zwischen 1 und {MAX_ERGEBNISSE} liegen")
        self.suchbegriff = suchbegriff
        self.limit = limit
        self.register = register or Register()
        self._umgebung = os.environ if umgebung is None else umgebung
        self._transport = transport or _anfrage
        self._jetzt = jetzt
        self._token_wert: str | None = None
        self._token_bis = 0.0
        self.hinweise: list[str] = []

    def __repr__(self) -> str:  # nie Zugangsdaten oder Token zeigen
        return f"EbayAdapter(suchbegriff={self.suchbegriff!r}, umgebung={self.umgebung_name()!r})"

    def umgebung_name(self) -> str:
        return "produktion" if self._umgebung.get(PRODUKTION_VARIABLE) == "ja" else "sandbox"

    def host(self) -> str:
        return PRODUKTION_HOST if self.umgebung_name() == "produktion" else SANDBOX_HOST

    def _freigegebenes_register(self) -> Register:
        """Der Schalter hebt nur „später“ auf „erlaubt“ – nie „ausgeschlossen“. Nur in einer Kopie."""
        q = self.register.get(self.kennung)
        if q is None or q.entscheidung != SPAETER:
            return self.register
        return Register([x for x in self.register if x.kennung != self.kennung]
                        + [Quelle(q.kennung, q.name, ERLAUBT, q.hinweis)])

    def _zugang(self, name: str) -> str:
        wert = self._umgebung.get(name)
        return wert.strip() if isinstance(wert, str) else ""

    def sperrgrund(self) -> str | None:
        q = self.register.get(self.kennung)
        if q is None or q.entscheidung == AUSGESCHLOSSEN:
            return self.register.pruefe(self.kennung)
        if self._umgebung.get(FREIGABE_VARIABLE) != "ja":
            return f"Freigabeschalter {FREIGABE_VARIABLE}=ja fehlt (Entscheidung von Jefrey)"
        fehlend = [n for n in (ID_VARIABLE, SECRET_VARIABLE) if not self._zugang(n)]
        if fehlend:
            return "Zugangsdaten fehlen: " + ", ".join(fehlend) + " (siehe docs/EBAY.md)"
        return self._freigegebenes_register().pruefe(self.kennung)

    def _token(self) -> str:
        if self._token_wert and time.monotonic() < self._token_bis:
            return self._token_wert
        paar = f"{self._zugang(ID_VARIABLE)}:{self._zugang(SECRET_VARIABLE)}".encode("utf-8")
        kopf = {
            "Authorization": "Basic " + base64.b64encode(paar).decode("ascii"),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        koerper = urllib.parse.urlencode({"grant_type": "client_credentials", "scope": SCOPE}).encode("ascii")
        antwort = self._transport("POST", f"https://{self.host()}{TOKEN_PFAD}", kopf, koerper)
        token = antwort.get("access_token") if isinstance(antwort, dict) else None
        dauer = antwort.get("expires_in") if isinstance(antwort, dict) else None
        if (not isinstance(token, str) or not re.fullmatch(r"[\x21-\x7e]+", token)
                or isinstance(dauer, bool) or not isinstance(dauer, int) or dauer <= 0):
            raise EbayFehler("Token-Antwort unbrauchbar")
        self._token_wert = token
        self._token_bis = time.monotonic() + max(dauer - 60, 0)
        return token

    def such_url(self) -> str:
        params = {
            "q": self.suchbegriff,
            "limit": str(self.limit),
            "filter": "deliveryCountry:DE,priceCurrency:EUR",
        }
        return f"https://{self.host()}{SUCH_PFAD}?" + urllib.parse.urlencode(params)

    def lade(self) -> Importergebnis:
        grund = self.sperrgrund()
        if grund:
            raise EbayGesperrt(grund)
        token = self._token()
        kopf = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": MARKTPLATZ,
            "Accept": "application/json",
            "Accept-Language": "de-DE",
        }
        antwort = self._transport("GET", self.such_url(), kopf, None)
        jetzt = self._jetzt or dt.datetime.now(dt.timezone.utc)
        zeilen, self.hinweise = zeilen_aus_antwort(antwort, self.umgebung_name(), jetzt)
        # Übersprungene Einträge sind keine Fehler, sondern stehen in self.hinweise.
        return lies_text(json.dumps(zeilen, ensure_ascii=False), "json", self._freigegebenes_register(),
                         jetzt=jetzt)
