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
