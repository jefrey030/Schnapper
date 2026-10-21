"""Suche, Filter und Sortierung über geprüfte Angebote."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal

from .angebot import Angebot, normalisiere_titel, warnungen

SORTIERUNGEN = ("rabatt", "preis", "neueste")


@dataclass
class Filter:
    text: str = ""
    max_preis: Decimal | None = None
    min_rabatt: Decimal | None = None
    zustaende: set[str] = field(default_factory=set)
    quellen: set[str] = field(default_factory=set)
    kategorie: str = ""
    ohne_verdacht: bool = True
    ohne_veraltet: bool = False
    max_alter_stunden: int = 24


@dataclass(frozen=True)
class Treffer:
    angebot: Angebot
    warnungen: tuple[str, ...]


def passt(angebot: Angebot, f: Filter, hinweise: list[str]) -> bool:
    if f.text:
        titel = set(normalisiere_titel(angebot.titel).split())
        if not all(w in titel for w in normalisiere_titel(f.text).split()):
            return False
    if f.max_preis is not None and angebot.gesamtpreis > f.max_preis:
        return False
    if f.min_rabatt is not None:
        rabatt = angebot.rabatt_prozent
        if rabatt is None or rabatt < f.min_rabatt:
            return False
    if f.zustaende and angebot.zustand not in f.zustaende:
        return False
    if f.quellen and angebot.quelle.lower() not in {q.lower() for q in f.quellen}:
        return False
    if f.kategorie and angebot.kategorie.lower() != f.kategorie.lower():
        return False
    if f.ohne_verdacht and any(h.startswith("betrugsverdacht") for h in hinweise):
        return False
    if f.ohne_veraltet and any(h.startswith("veraltet") for h in hinweise):
        return False
    return True


def suche(angebote: list[Angebot], f: Filter | None = None, sortierung: str = "rabatt",
          jetzt: dt.datetime | None = None) -> list[Treffer]:
    if sortierung not in SORTIERUNGEN:
        raise ValueError(f"Sortierung muss eine von {SORTIERUNGEN} sein")
    f = f or Filter()
    treffer = []
    for a in angebote:
        hinweise = warnungen(a, jetzt=jetzt, max_alter_stunden=f.max_alter_stunden)
        if passt(a, f, hinweise):
            treffer.append(Treffer(a, tuple(hinweise)))
    if sortierung == "preis":
        treffer.sort(key=lambda t: (t.angebot.gesamtpreis, t.angebot.id))
    elif sortierung == "neueste":
        treffer.sort(key=lambda t: (t.angebot.erfasst_am, t.angebot.id), reverse=True)
    else:  # höchster belegter Rabatt zuerst, Angebote ohne Referenzpreis ans Ende
        treffer.sort(key=lambda t: (t.angebot.rabatt_prozent is None,
                                    -(t.angebot.rabatt_prozent or 0), t.angebot.gesamtpreis, t.angebot.id))
    return treffer
