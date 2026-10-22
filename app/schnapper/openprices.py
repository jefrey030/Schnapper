"""Open-Prices-Adapter (Quelle Q5): echte, von Menschen gemeldete Ladenpreise.

Open Prices ist ein Projekt von Open Food Facts. Die Daten stehen unter der
Open Database License (ODbL): Quellenangabe erforderlich; Share-Alike kann
bei öffentlicher Nutzung einer angepassten Datenbank greifen.
SCHNAPPER zeigt die Preise isoliert an und speichert sie nicht dauerhaft.

Kosten: 0 €, kein Konto, kein Schlüssel.
Netzwerk nur, wenn SCHNAPPER_OPENPRICES_FREIGABE=ja gesetzt ist (Jefreys Entscheidung).
Nur Host prices.openfoodfacts.org, nur HTTPS, eigene Kennung im User-Agent (Pflicht laut Open Food Facts).

Belege: https://openfoodfacts.github.io/documentation/docs/Open-prices/prices/prices_list/
        https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation

from .einlesen import Importergebnis, lies_text
from .quellen import AUSGESCHLOSSEN, ERLAUBT, SPAETER, Quelle, Register

HOST = "prices.openfoodfacts.org"
API = f"https://{HOST}/api/v1/prices"
FREIGABE_VARIABLE = "SCHNAPPER_OPENPRICES_FREIGABE"
USER_AGENT = "SCHNAPPER/0.1 (privates Testprojekt; github.com/jefrey030)"
LIZENZ = "Preise: Open Prices (Open Food Facts), Lizenz ODbL – prices.openfoodfacts.org"
EAN = re.compile(r"^\d{8,14}$")
MAX_ERGEBNISSE = 50


class OpenPricesGesperrt(RuntimeError):
    """Abruf nicht erlaubt (Schalter fehlt oder Quelle gesperrt)."""


class OpenPricesFehler(RuntimeError):
    """Antwort unbrauchbar oder Dienst nicht erreichbar."""


def anfrage_url(ean: str, tage: int = 90, heute: dt.date | None = None, seite: int = 1) -> str:
    if not EAN.match(ean or ""):
        raise ValueError("EAN/Barcode muss aus 8 bis 14 Ziffern bestehen")
    if not 1 <= tage <= 3650:
        raise ValueError("Zeitraum muss zwischen 1 und 3650 Tagen liegen")
    heute = heute or dt.date.today()
    params = {
        "product_code": ean,
        "currency": "EUR",
        "date__gte": (heute - dt.timedelta(days=tage)).isoformat(),
        "order_by": "-date",
        "duplicate_of__isnull": "true",
        "size": str(MAX_ERGEBNISSE),
        "page": str(seite),
    }
    return API + "?" + urllib.parse.urlencode(params)


def _preis(wert) -> Decimal | None:
    """Keine NaN/Infinity, Bool-Werte oder Beträge außerhalb der Angebotsgrenzen."""
    if isinstance(wert, bool):
        return None
    try:
        d = Decimal(str(wert))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return d if d.is_finite() and Decimal("0.005") <= d <= Decimal("1000000") else None


def zeilen_aus_antwort(antwort: dict, ean: str, jetzt: dt.datetime | None = None) -> tuple[list[dict], list[str]]:
    """Wandelt eine Open-Prices-Antwort in SCHNAPPER-Rohzeilen. Unpassendes wird übersprungen und gemeldet."""
    if not isinstance(antwort, dict) or not isinstance(antwort.get("items"), list):
        raise OpenPricesFehler("Antwort ohne 'items'-Liste – Format hat sich geändert?")
    zeilen, hinweise = [], []
    for item in antwort["items"]:
        if not isinstance(item, dict):
            hinweise.append("Eintrag ohne Objektstruktur übersprungen")
            continue
        pid = item.get("id")
        kennung = f"Preis {pid}"
        if item.get("product_code") != ean:
            hinweise.append(f"{kennung}: anderer Barcode – übersprungen")
            continue
        if item.get("currency") != "EUR":
            hinweise.append(f"{kennung}: Währung {item.get('currency')} – übersprungen")
            continue
        if item.get("price_per") not in (None, "UNIT"):
            hinweise.append(f"{kennung}: Preis pro {item.get('price_per')} statt Stückpreis – übersprungen")
            continue
        if item.get("duplicate_of"):
            hinweise.append(f"{kennung}: als Dublette markiert – übersprungen")
            continue
        preis = _preis(item.get("price"))
        if preis is None or isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            hinweise.append(f"{kennung}: ohne gültigen Preis oder ID – übersprungen")
            continue
        try:
            beobachtet = dt.date.fromisoformat(str(item.get("date")))
        except ValueError:
            hinweise.append(f"{kennung}: ohne gültiges Datum – übersprungen")
            continue
        produkt = item.get("product")
        ort = item.get("location")
        produkt = produkt if isinstance(produkt, dict) else {}
        ort = ort if isinstance(ort, dict) else {}
        namen = (item.get("product_name"), produkt.get("product_name"))
        name = next((x.strip() for x in namen if isinstance(x, str) and x.strip()), f"Produkt {ean}")
        laden = " · ".join(x.strip() for x in (ort.get("osm_name"), ort.get("osm_address_city"))
                           if isinstance(x, str) and x.strip())
        referenz = _preis(item.get("price_without_discount")) if item.get("price_is_discounted") else None
        zeilen.append({
            "id": f"openprices-{pid}",
            "titel": f"{name} – {laden}" if laden else name,
            "preis": str(preis),
            "referenzpreis": "" if referenz is None or referenz <= preis else str(referenz),
            "versand": "0",
            "url": f"{API}/{pid}",
            "quelle": "openprices",
            # Beobachtungstag, Tagesbeginn UTC – höchstens „jetzt“, denn ein Datum aus einer Zeitzone
            # östlich von UTC kann kurz nach Mitternacht noch in der UTC-Zukunft liegen.
            "erfasst_am": min(dt.datetime.combine(beobachtet, dt.time(0), dt.timezone.utc),
                              jetzt or dt.datetime.now(dt.timezone.utc)).isoformat(),
            "zustand": "neu",
            "kategorie": "Ladenpreis",
            "ean": ean,
            "laden": laden,
            "land": ort.get("osm_address_country_code") or "",
            "lizenz": LIZENZ,
        })
    return zeilen, hinweise


def _abruf(url: str, timeout: float = 15.0) -> dict:
    teile = urllib.parse.urlsplit(url)
    if teile.scheme != "https" or teile.hostname != HOST:
        raise OpenPricesGesperrt(f"Nur https://{HOST} ist erlaubt")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})

    class KeineWeiterleitung(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener(KeineWeiterleitung)
    try:
        with opener.open(req, timeout=timeout) as antwort:
            if antwort.status != 200:
                raise OpenPricesFehler(f"HTTP {antwort.status}")
            roh = antwort.read(2_000_001)
    except OSError as exc:  # URLError, Timeout, HTTPError
        raise OpenPricesFehler(f"Open Prices nicht erreichbar: {exc}") from exc
    if len(roh) > 2_000_000:
        raise OpenPricesFehler("Antwort zu groß")
    try:
        return json.loads(roh)
    except json.JSONDecodeError as exc:
        raise OpenPricesFehler("Antwort ist kein JSON") from exc


class OpenPricesAdapter:
    """Echte Ladenpreise zu einem Barcode. `abruf` ist austauschbar (Tests ohne Netz)."""

    kennung = "openprices"

    def __init__(self, ean: str, tage: int = 90, register: Register | None = None, abruf=None, umgebung=None):
        self.ean = (ean or "").strip()
        self.tage = tage
        self.register = register or Register()
        self._abruf = abruf or _abruf
        self._umgebung = os.environ if umgebung is None else umgebung
        anfrage_url(self.ean, tage)  # prüft Eingaben sofort
        self.hinweise: list[str] = []

    def _freigegebenes_register(self) -> Register:
        """Der Schalter hebt nur „später“ auf „erlaubt“ – nie „ausgeschlossen“."""
        q = self.register.get(self.kennung)
        if q is None or q.entscheidung != SPAETER:
            return self.register
        return Register([x for x in self.register if x.kennung != self.kennung]
                        + [Quelle(q.kennung, q.name, ERLAUBT, q.hinweis)])

    def sperrgrund(self) -> str | None:
        q = self.register.get(self.kennung)
        if q is not None and q.entscheidung == AUSGESCHLOSSEN:
            return self.register.pruefe(self.kennung)
        if self._umgebung.get(FREIGABE_VARIABLE) != "ja":
            return f"Freigabeschalter {FREIGABE_VARIABLE}=ja fehlt (Entscheidung von Jefrey)"
        return self._freigegebenes_register().pruefe(self.kennung)

    def lade(self) -> Importergebnis:
        grund = self.sperrgrund()
        if grund:
            raise OpenPricesGesperrt(grund)
        antwort = self._abruf(anfrage_url(self.ean, self.tage))
        zeilen, self.hinweise = zeilen_aus_antwort(antwort, self.ean)
        # Übersprungene Einträge sind keine Fehler, sondern stehen in self.hinweise.
        return lies_text(json.dumps(zeilen, ensure_ascii=False), "json", self._freigegebenes_register())
