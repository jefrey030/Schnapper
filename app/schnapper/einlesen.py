"""Angebote aus Dateien einlesen (JSON oder CSV).

Es wird bewusst NICHT im Internet gesucht oder gescrapt. Angebote kommen aus
Dateien, deren Herkunft und Nutzungsrechte vorher geklärt sind (z. B. ein
offizieller Partner-Feed oder eine selbst gepflegte Liste). Ungültige Zeilen
brechen den Import nicht ab, sondern werden mit Grund gemeldet.
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
from dataclasses import dataclass, field

from .angebot import Angebot, AngebotFehler
from .quellen import QuellenFehler, Register

MAX_DATEIGROESSE = 20 * 1024 * 1024  # 20 MB


@dataclass
class Importergebnis:
    angebote: list[Angebot] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def _zeilen_json(text: str) -> list:
    daten = json.loads(text)
    if isinstance(daten, dict):
        daten = daten.get("angebote")
    if not isinstance(daten, list):
        raise AngebotFehler("JSON muss eine Liste oder {\"angebote\": [...]} sein")
    return daten


def _zeilen_csv(text: str) -> list:
    try:
        dialekt = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
    except csv.Error:
        dialekt = csv.excel
    return list(csv.DictReader(io.StringIO(text), dialect=dialekt))


def lies_text(text: str, format: str, register: Register | None = None, jetzt=None) -> Importergebnis:
    """Nur Angebote aus freigegebenen Quellen werden übernommen (Plan S-002, MF1)."""
    register = Register() if register is None else register
    ergebnis = Importergebnis()
    try:
        zeilen = _zeilen_json(text) if format == "json" else _zeilen_csv(text)
    except (json.JSONDecodeError, AngebotFehler) as exc:
        ergebnis.fehler.append(f"Datei: {exc}")
        return ergebnis
    gesehen: set[str] = set()
    for nr, zeile in enumerate(zeilen, start=1):
        try:
            angebot = Angebot.aus_dict(zeile, jetzt)
        except AngebotFehler as exc:
            ergebnis.fehler.append(f"Eintrag {nr}: {exc}")
            continue
        grund = register.pruefe(angebot.quelle)
        if grund:
            ergebnis.fehler.append(f"Eintrag {nr}: {grund}")
            continue
        if angebot.id in gesehen:
            ergebnis.fehler.append(f"Eintrag {nr}: ID '{angebot.id}' doppelt vergeben")
            continue
        gesehen.add(angebot.id)
        ergebnis.angebote.append(angebot)
    return ergebnis


def lies_datei(pfad, register: Register | None = None) -> Importergebnis:
    """Liegt neben der Datei eine quellen.json, werden deren Freigaben zusätzlich geladen."""
    pfad = pathlib.Path(pfad)
    if register is None and (pfad.parent / "quellen.json").is_file():
        try:
            register = Register.mit_datei(pfad.parent / "quellen.json")
        except (QuellenFehler, ValueError) as exc:
            return Importergebnis(fehler=[f"quellen.json: {exc}"])
    if pfad.stat().st_size > MAX_DATEIGROESSE:
        return Importergebnis(fehler=[f"Datei größer als {MAX_DATEIGROESSE // 1024 // 1024} MB"])
    endung = pfad.suffix.lower()
    if endung not in (".json", ".csv"):
        return Importergebnis(fehler=["Nur .json oder .csv werden unterstützt"])
    text = pfad.read_text(encoding="utf-8-sig")
    return lies_text(text, "json" if endung == ".json" else "csv", register)
