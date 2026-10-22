"""Quellen-Adapter (Plan S-002, MF2) und der gemeinsame Suchablauf.

Ein Adapter liefert geprüfte Angebote aus genau einer Art von Quelle.
Der Ablauf ist immer gleich: laden -> Quellen prüfen -> Dubletten entfernen ->
filtern/sortieren. Weder Tests noch der Datei-Adapter greifen auf das Netz zu.
"""
from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field

from .angebot import Angebot
from .dubletten import entferne_dubletten
from .einlesen import Importergebnis, lies_datei
from .quellen import Register
from .suche import Filter, Treffer, suche


class QuelleGesperrt(RuntimeError):
    """Der Adapter darf (noch) nicht benutzt werden."""


class DateiAdapter:
    """Angebote aus einer lokalen .json/.csv (Quellen Q3 eigene Daten / Q4 Testdaten)."""

    def __init__(self, pfad, register: Register | None = None):
        self.pfad = pathlib.Path(pfad)
        self.register = register
        self.kennung = "datei:" + self.pfad.name

    def lade(self) -> Importergebnis:
        return lies_datei(self.pfad, self.register)




class MockAdapter:
    """Reine Offline-Testquelle (S-005/T3), niemals echte Marktpreise.

    Ohne Konfiguration liefert der Adapter genau zwei als TEST markierte
    Beispielangebote mit .invalid-URLs. Es finden keine Netzwerkanfragen,
    kein Scraping und keine Dateischreibvorgänge statt.
    """

    kennung = "mock"

    def __init__(self, daten=None, register: Register | None = None, jetzt=None):
        import datetime as dt

        self.register = register if register is not None else Register()
        self.jetzt = jetzt or dt.datetime.now(dt.timezone.utc)
        if self.jetzt.tzinfo is None:
            raise ValueError("Mock-Zeitpunkt muss eine Zeitzone enthalten")
        if daten is not None and not isinstance(daten, list):
            raise ValueError("Mock-Daten müssen eine Liste sein")
        self.daten = daten

    def lade(self) -> Importergebnis:
        import datetime as dt
        import json

        grund = self.register.pruefe(self.kennung)
        if grund:
            raise QuelleGesperrt(grund)
        daten = self.daten
        if daten is None:
            aktuell = self.jetzt.astimezone(dt.timezone.utc).isoformat()
            alt = (self.jetzt - dt.timedelta(hours=27)).astimezone(dt.timezone.utc).isoformat()
            daten = [
                {"id": "TEST-1", "titel": "TEST Fahrrad gebraucht",
                 "preis": "45.00", "referenzpreis": "80.00", "versand": "0",
                 "url": "https://example.invalid/schnapper/test-1",
                 "quelle": "mock", "erfasst_am": aktuell, "zustand": "gebraucht"},
                {"id": "TEST-2", "titel": "TEST Kopfhörer gebraucht",
                 "preis": "25.00", "referenzpreis": "55.00", "versand": "4.90",
                 "url": "https://example.invalid/schnapper/test-2",
                 "quelle": "mock", "erfasst_am": alt, "zustand": "gebraucht"},
            ]
        if any(not isinstance(zeile, dict) or str(zeile.get("quelle", "")).lower() != "mock"
               for zeile in daten):
            raise QuelleGesperrt("MockAdapter darf ausschließlich Testangebote der Quelle 'mock' verarbeiten")
        from .einlesen import lies_text
        return lies_text(json.dumps(daten, ensure_ascii=False), "json", self.register)


class EbayAdapter:
    """Platzhalter für die eBay Browse API (Q1).

    Bewusst NICHT umgesetzt: Produktivnutzung braucht eine Genehmigung von eBay
    und Jefreys Freigabe. Bis dahin wird nie ein Netzwerkaufruf gemacht.
    """
    kennung = "ebay"
    FREIGABE_VARIABLE = "SCHNAPPER_EBAY_FREIGABE"

    def __init__(self, register: Register | None = None):
        self.register = register or Register()

    def sperrgrund(self) -> str:
        grund = self.register.pruefe("ebay")
        if grund:
            return grund
        if os.environ.get(self.FREIGABE_VARIABLE) != "ja":
            return f"Freigabeschalter {self.FREIGABE_VARIABLE}=ja fehlt"
        return "eBay-Anbindung ist noch nicht programmiert"

    def lade(self) -> Importergebnis:
        raise QuelleGesperrt(self.sperrgrund())


@dataclass
class Suchergebnis:
    treffer: list[Treffer] = field(default_factory=list)
    eingelesen: int = 0
    fehler: list[str] = field(default_factory=list)
    dubletten: list[tuple[Angebot, Angebot]] = field(default_factory=list)


def finde(adapter, f: Filter | None = None, sortierung: str = "rabatt", jetzt=None) -> Suchergebnis:
    """Kompletter Suchablauf über einen Adapter."""
    geladen = adapter.lade()
    return finde_in(geladen, f, sortierung, jetzt)


def finde_in(geladen: Importergebnis, f: Filter | None = None, sortierung: str = "rabatt", jetzt=None) -> Suchergebnis:
    eindeutig, dubletten = entferne_dubletten(geladen.angebote)
    return Suchergebnis(treffer=suche(eindeutig, f, sortierung, jetzt=jetzt), eingelesen=len(geladen.angebote),
                        fehler=list(geladen.fehler), dubletten=dubletten)
