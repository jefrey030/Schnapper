"""Sichere, lokale Suchaufträge (MISSION) für vorbereitete Suchzyklen.

Dieses Modul verwaltet Aufträge und berechnet, welche davon fällig sind. Es
startet keinen Hintergrundprozess und greift nicht auf externe Dienste zu.
Ein Scheduler kann ``faellige()`` abfragen und die zurückgegebenen Filter mit
dem vorhandenen Angebotsadapter ausführen.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import threading
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .angebot import AngebotFehler, ZUSTAENDE, geld
from .suche import Filter
from .sicherer_speicher import dateisperre, digest, lese_fd, schreibe_fd

FORMAT_VERSION = 2
MAX_MISSIONEN = 100
MIN_INTERVALL_MINUTEN = 15
MAX_INTERVALL_MINUTEN = 7 * 24 * 60
_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_STATUS = frozenset({"aktiv", "pausiert", "beendet"})


class MissionsFehler(ValueError):
    """Ein Suchauftrag ist ungültig oder kann nicht sicher geladen werden."""


class MissionsKonflikt(MissionsFehler):
    """Ein anderer Speicherprozess hat seit dem letzten Lesen Änderungen gespeichert."""


def _zeit(wert: dt.datetime | str | None, standard: dt.datetime | None = None) -> dt.datetime:
    if wert is None:
        wert = standard or dt.datetime.now(dt.timezone.utc)
    if isinstance(wert, str):
        try:
            wert = dt.datetime.fromisoformat(wert)
        except ValueError as exc:
            raise MissionsFehler("Zeitstempel ist ungültig") from exc
    if not isinstance(wert, dt.datetime) or wert.tzinfo is None or wert.utcoffset() is None:
        raise MissionsFehler("Zeitstempel muss eine Zeitzone enthalten")
    return wert.astimezone(dt.timezone.utc)


def _preis(wert) -> Decimal | None:
    if wert in (None, ""):
        return None
    try:
        betrag = geld(wert)
    except AngebotFehler as exc:
        raise MissionsFehler("Höchstpreis ist ungültig") from exc
    if betrag <= 0:
        raise MissionsFehler("Höchstpreis muss größer als 0 sein")
    return betrag


def _rabatt(wert) -> Decimal | None:
    if wert in (None, ""):
        return None
    try:
        betrag = Decimal(str(wert).replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise MissionsFehler("Mindestrabatt ist ungültig") from exc
    if not betrag.is_finite() or not Decimal("0") <= betrag <= Decimal("100"):
        raise MissionsFehler("Mindestrabatt muss zwischen 0 und 100 liegen")
    return betrag


def _entfernung(wert) -> Decimal | None:
    if wert in (None, ""):
        return None
    try:
        betrag = Decimal(str(wert).replace(",", "."))
    except (InvalidOperation, AttributeError) as exc:
        raise MissionsFehler("Entfernung ist ungültig") from exc
    if not betrag.is_finite() or not Decimal("0") <= betrag <= Decimal("500"):
        raise MissionsFehler("Entfernung muss zwischen 0 und 500 km liegen")
    return betrag


@dataclass(frozen=True)
class Mission:
    id: str
    name: str
    suche: str
    max_preis: Decimal | None
    min_rabatt: Decimal | None
    zustaende: frozenset[str]
    intervall_minuten: int
    status: str
    erstellt_am: dt.datetime
    letzter_lauf_am: dt.datetime | None = None
    region: str = ""
    entfernung_km: Decimal | None = None
    automatisch: bool = False

    @classmethod
    def erstellen(cls, name: str, suche: str, max_preis=None, min_rabatt=None,
                  zustaende=(), intervall_minuten: int = 60, jetzt=None,
                  mission_id: str | None = None, region: str = "",
                  entfernung_km=None, automatisch: bool = False) -> "Mission":
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            raise MissionsFehler("Name muss 1 bis 100 Zeichen enthalten")
        if not isinstance(suche, str) or not suche.strip() or len(suche.strip()) > 200:
            raise MissionsFehler("Suchbegriff muss 1 bis 200 Zeichen enthalten")
        if isinstance(intervall_minuten, bool) or not isinstance(intervall_minuten, int):
            raise MissionsFehler("Intervall muss eine ganze Minutenzahl sein")
        if not MIN_INTERVALL_MINUTEN <= intervall_minuten <= MAX_INTERVALL_MINUTEN:
            raise MissionsFehler(
                f"Intervall muss zwischen {MIN_INTERVALL_MINUTEN} und {MAX_INTERVALL_MINUTEN} Minuten liegen")
        if not isinstance(region, str) or len(region.strip()) > 100:
            raise MissionsFehler("Region darf höchstens 100 Zeichen enthalten")
        if not isinstance(automatisch, bool):
            raise MissionsFehler("Automatik muss Ja oder Nein sein")
        if isinstance(zustaende, str):
            zustaende = [zustaende]
        if not isinstance(zustaende, (list, tuple, set, frozenset)):
            raise MissionsFehler("Zustände müssen als Liste oder Text angegeben werden")
        zustand_set = frozenset(str(z).strip().lower() for z in zustaende if str(z).strip())
        unbekannt = zustand_set - set(ZUSTAENDE)
        if unbekannt:
            raise MissionsFehler(f"Unbekannter Zustand: {', '.join(sorted(unbekannt))}")
        ident = mission_id or uuid.uuid4().hex
        if not isinstance(ident, str) or not _ID.fullmatch(ident):
            raise MissionsFehler("Missions-ID ist ungültig")
        return cls(
            id=ident,
            name=name.strip(),
            suche=suche.strip(),
            max_preis=_preis(max_preis),
            min_rabatt=_rabatt(min_rabatt),
            zustaende=zustand_set,
            intervall_minuten=intervall_minuten,
            status="aktiv",
            erstellt_am=_zeit(jetzt),
            region=region.strip(),
            entfernung_km=_entfernung(entfernung_km),
            automatisch=automatisch,
        )

    def filter(self) -> Filter:
        return Filter(text=self.suche, max_preis=self.max_preis, min_rabatt=self.min_rabatt,
                      zustaende=set(self.zustaende), region=self.region,
                      entfernung_km=self.entfernung_km,
                      ohne_verdacht=True, ohne_veraltet=True)

    def ist_faellig(self, jetzt=None) -> bool:
        if self.status != "aktiv":
            return False
        if self.letzter_lauf_am is None:
            return True
        return _zeit(jetzt) >= self.letzter_lauf_am + dt.timedelta(minutes=self.intervall_minuten)

    def als_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "suche": self.suche,
            "max_preis": None if self.max_preis is None else str(self.max_preis),
            "min_rabatt": None if self.min_rabatt is None else str(self.min_rabatt),
            "zustaende": sorted(self.zustaende), "intervall_minuten": self.intervall_minuten,
            "status": self.status, "erstellt_am": self.erstellt_am.isoformat(),
            "letzter_lauf_am": None if self.letzter_lauf_am is None else self.letzter_lauf_am.isoformat(),
            "region": self.region,
            "entfernung_km": None if self.entfernung_km is None else str(self.entfernung_km),
            "automatisch": self.automatisch,
        }

    @classmethod
    def aus_dict(cls, daten: dict) -> "Mission":
        if not isinstance(daten, dict):
            raise MissionsFehler("Mission muss ein Objekt sein")
        try:
            mission = cls.erstellen(
                name=daten["name"], suche=daten["suche"], max_preis=daten.get("max_preis"),
                min_rabatt=daten.get("min_rabatt"), zustaende=daten.get("zustaende", []),
                intervall_minuten=daten["intervall_minuten"], jetzt=daten["erstellt_am"],
                mission_id=daten["id"],
                region=daten.get("region", ""), entfernung_km=daten.get("entfernung_km"),
                automatisch=daten.get("automatisch", False),
            )
            status = daten["status"]
            if status not in _STATUS:
                raise MissionsFehler("Missionsstatus ist ungültig")
            letzter = daten.get("letzter_lauf_am")
            letzter = None if letzter is None else _zeit(letzter)
            if letzter is not None and letzter < mission.erstellt_am:
                raise MissionsFehler("Letzter Lauf liegt vor der Erstellung")
            return cls(**{**mission.__dict__, "status": status, "letzter_lauf_am": letzter})
        except (KeyError, TypeError) as exc:
            raise MissionsFehler("Missionsdaten sind unvollständig") from exc


class Missionsspeicher:
    """Versionierter, konfliktprüfender und verzeichnissicherer Missionsspeicher."""

    def __init__(self, pfad: pathlib.Path | str, missionen: list[Mission] | None = None,
                 _revision: str | None = None):
        self.pfad = pathlib.Path(pfad)
        self._lock = threading.RLock()
        self._missionen = list(missionen or [])
        self._revision = _revision
        self._pruefe_gesamt(self._missionen)

    @classmethod
    def _dekodiere(cls, raw: bytes | None, dateiname: str) -> tuple[list[Mission], str | None]:
        if raw is None:
            return [], None
        try:
            daten = json.loads(raw.decode("utf-8"))
            if (not isinstance(daten, dict) or type(daten.get("version")) is not int
                    or daten.get("version") not in (1, FORMAT_VERSION)
                    or not isinstance(daten.get("missionen"), list)):
                raise MissionsFehler("Unbekanntes Missionsdateiformat")
            missionen = [Mission.aus_dict(x) for x in daten["missionen"]]
            cls._pruefe_gesamt(missionen)
            return missionen, digest(raw)
        except MissionsFehler as exc:
            raise MissionsFehler(f"{dateiname}: {exc}") from exc
        except (OSError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise MissionsFehler(f"{dateiname} ist beschädigt und wird nicht überschrieben") from exc

    @classmethod
    def dekodiere_snapshot(cls, raw: bytes | None) -> tuple[list[Mission], str | None]:
        """Validiert einen MISSION-Snapshot, dessen Dateien bereits sicher gelesen wurden."""
        return cls._dekodiere(raw, "missionen.json")

    @classmethod
    def laden(cls, pfad: pathlib.Path | str) -> "Missionsspeicher":
        datei = pathlib.Path(pfad)
        try:
            with dateisperre(datei) as (directory, name):
                missionen, revision = cls._dekodiere(lese_fd(directory, name), datei.name)
            return cls(datei, missionen, revision)
        except MissionsFehler:
            raise
        except OSError as exc:
            raise MissionsFehler(f"{datei.name} kann nicht sicher gelesen werden") from exc

    @staticmethod
    def _pruefe_gesamt(missionen: list[Mission]) -> None:
        if len(missionen) > MAX_MISSIONEN:
            raise MissionsFehler(f"Höchstens {MAX_MISSIONEN} Missionen")
        ids = [m.id for m in missionen]
        if len(ids) != len(set(ids)):
            raise MissionsFehler("Missions-IDs müssen eindeutig sein")

    def alle(self) -> tuple[Mission, ...]:
        with self._lock:
            try:
                with dateisperre(self.pfad) as (directory, name):
                    self._missionen, self._revision = self._dekodiere(
                        lese_fd(directory, name), self.pfad.name)
                    return tuple(self._missionen)
            except MissionsFehler:
                raise
            except OSError as exc:
                raise MissionsFehler(f"{self.pfad.name} kann nicht sicher gelesen werden") from exc

    def exportdaten(self) -> dict:
        return {"version": FORMAT_VERSION, "missionen": [m.als_dict() for m in self.alle()]}

    def faellige(self, jetzt=None) -> tuple[Mission, ...]:
        zeit = _zeit(jetzt)
        return tuple(m for m in self.alle() if m.ist_faellig(zeit))

    def _transaktion(self, aendern):
        with self._lock:
            try:
                with dateisperre(self.pfad) as (directory, name):
                    missionen, revision = self._dekodiere(lese_fd(directory, name), self.pfad.name)
                    if revision != self._revision:
                        self._missionen, self._revision = missionen, revision
                        raise MissionsKonflikt(
                            "Missionen wurden parallel geändert; Daten neu laden und Änderung erneut prüfen")
                    neu, ergebnis = aendern(list(missionen))
                    self._pruefe_gesamt(neu)
                    raw = json.dumps(
                        {"version": FORMAT_VERSION, "missionen": [m.als_dict() for m in neu]},
                        ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8")
                    schreibe_fd(directory, name, raw)
                    self._missionen, self._revision = neu, digest(raw)
                    return ergebnis
            except (MissionsFehler, MissionsKonflikt):
                raise
            except OSError as exc:
                raise MissionsFehler("Mission konnte lokal nicht sicher gespeichert werden") from exc

    def erstellen(self, **daten) -> Mission:
        mission = Mission.erstellen(**daten)
        return self._transaktion(lambda liste: ([*liste, mission], mission))

    def bearbeiten(self, mission_id: str, **daten) -> Mission:
        def aendern(liste):
            index = next((i for i, m in enumerate(liste) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = liste[index]
            neu = Mission.erstellen(
                name=daten.get("name", alt.name), suche=daten.get("suche", alt.suche),
                max_preis=daten.get("max_preis", alt.max_preis),
                min_rabatt=daten.get("min_rabatt", alt.min_rabatt),
                zustaende=daten.get("zustaende", alt.zustaende),
                intervall_minuten=daten.get("intervall_minuten", alt.intervall_minuten),
                region=daten.get("region", alt.region),
                entfernung_km=daten.get("entfernung_km", alt.entfernung_km),
                automatisch=daten.get("automatisch", alt.automatisch),
                jetzt=alt.erstellt_am, mission_id=alt.id)
            neu = Mission(**{**neu.__dict__, "status": alt.status, "letzter_lauf_am": alt.letzter_lauf_am})
            liste[index] = neu
            return liste, neu
        return self._transaktion(aendern)

    def _status(self, mission_id: str, status: str) -> Mission:
        def aendern(liste):
            index = next((i for i, m in enumerate(liste) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = liste[index]
            if alt.status == "beendet" and status != "beendet":
                raise MissionsFehler("Beendete Missionen können nicht reaktiviert werden")
            neu = Mission(**{**alt.__dict__, "status": status})
            liste[index] = neu
            return liste, neu
        return self._transaktion(aendern)

    def pausieren(self, mission_id: str) -> Mission:
        return self._status(mission_id, "pausiert")

    def fortsetzen(self, mission_id: str) -> Mission:
        return self._status(mission_id, "aktiv")

    def beenden(self, mission_id: str) -> Mission:
        return self._status(mission_id, "beendet")

    def loeschen(self, mission_id: str) -> None:
        def aendern(liste):
            neu = [m for m in liste if m.id != mission_id]
            if len(neu) == len(liste):
                raise MissionsFehler("Mission nicht gefunden")
            return neu, None
        self._transaktion(aendern)

    def lauf_abschliessen(self, mission_id: str, jetzt=None, erzwingen: bool = False) -> Mission:
        zeit = _zeit(jetzt)
        def aendern(liste):
            index = next((i for i, m in enumerate(liste) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = liste[index]
            if not erzwingen and not alt.ist_faellig(zeit):
                raise MissionsFehler("Mission ist nicht aktiv oder noch nicht fällig")
            neu = Mission(**{**alt.__dict__, "letzter_lauf_am": zeit})
            liste[index] = neu
            return liste, neu
        return self._transaktion(aendern)
