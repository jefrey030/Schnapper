"""Dubletten-Erkennung.

Zwei Einträge gelten als dasselbe Inserat, wenn
  1. ihre URL nach Bereinigung (Tracking-Parameter, www., Schrägstrich) gleich ist, oder
  2. sie aus derselben Quelle stammen, ihre Titel fast gleich sind
     (Wort-Ähnlichkeit >= Schwelle) und der Gesamtpreis höchstens 2 % abweicht.
Gleiche Produkte bei VERSCHIEDENEN Quellen sind keine Dubletten, sondern
Vergleichsangebote, und bleiben erhalten.
Von jeder Dubletten-Gruppe bleibt der zuletzt erfasste Eintrag stehen.
"""
from __future__ import annotations

from decimal import Decimal

from .angebot import Angebot, normalisiere_titel, normalisiere_url

TITEL_SCHWELLE = 0.85
PREIS_TOLERANZ = Decimal("0.02")


def titel_aehnlichkeit(a: str, b: str) -> float:
    wa, wb = set(normalisiere_titel(a).split()), set(normalisiere_titel(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def sind_dubletten(a: Angebot, b: Angebot) -> bool:
    if normalisiere_url(a.url) == normalisiere_url(b.url):
        return True
    if a.quelle.lower() != b.quelle.lower():
        return False
    hoeher = max(a.gesamtpreis, b.gesamtpreis)
    if abs(a.gesamtpreis - b.gesamtpreis) > hoeher * PREIS_TOLERANZ:
        return False
    return titel_aehnlichkeit(a.titel, b.titel) >= TITEL_SCHWELLE


def entferne_dubletten(angebote: list[Angebot]) -> tuple[list[Angebot], list[tuple[Angebot, Angebot]]]:
    """Gibt (eindeutige Angebote, [(entfernt, behalten), ...]) zurück. Reihenfolge stabil."""
    behalten: list[Angebot] = []
    entfernt: list[tuple[Angebot, Angebot]] = []
    for neu in sorted(angebote, key=lambda x: x.erfasst_am, reverse=True):
        treffer = next((b for b in behalten if sind_dubletten(neu, b)), None)
        if treffer is None:
            behalten.append(neu)
        else:
            entfernt.append((neu, treffer))
    reihenfolge = {id(x): i for i, x in enumerate(angebote)}
    behalten.sort(key=lambda x: reihenfolge[id(x)])
    return behalten, entfernt
