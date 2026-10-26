"""Sichere, lokale Suchaufträge (MISSION) für vorbereitete Suchzyklen.

Dieses Modul verwaltet Aufträge und berechnet, welche davon fällig sind. Es
startet keinen Hintergrundprozess und greift nicht auf externe Dienste zu.
Ein Scheduler kann ``faellige()`` abfragen und die zurückgegebenen Filter mit
dem vorhandenen Angebotsadapter ausführen.
"""
from __future__ import annotations

import datetime as dt
import json
import stat
from contextlib import contextmanager
import os
import pathlib
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .angebot import AngebotFehler, ZUSTAENDE, geld
from .suche import Filter

FORMAT_VERSION = 1
MAX_MISSIONEN = 100
MIN_INTERVALL_MINUTEN = 15
MAX_INTERVALL_MINUTEN = 7 * 24 * 60
_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_STATUS = frozenset({"aktiv", "pausiert", "beendet"})


class MissionsFehler(ValueError):
    """Ein Suchauftrag ist ungültig oder kann nicht sicher geladen werden."""


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

    @classmethod
    def erstellen(cls, name: str, suche: str, max_preis=None, min_rabatt=None,
                  zustaende=(), intervall_minuten: int = 60, jetzt=None,
                  mission_id: str | None = None) -> "Mission":
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
            raise MissionsFehler("Name muss 1 bis 100 Zeichen enthalten")
        if not isinstance(suche, str) or not suche.strip() or len(suche.strip()) > 200:
            raise MissionsFehler("Suchbegriff muss 1 bis 200 Zeichen enthalten")
        if isinstance(intervall_minuten, bool) or not isinstance(intervall_minuten, int):
            raise MissionsFehler("Intervall muss eine ganze Minutenzahl sein")
        if not MIN_INTERVALL_MINUTEN <= intervall_minuten <= MAX_INTERVALL_MINUTEN:
            raise MissionsFehler(
                f"Intervall muss zwischen {MIN_INTERVALL_MINUTEN} und {MAX_INTERVALL_MINUTEN} Minuten liegen")
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
        )

    def filter(self) -> Filter:
        return Filter(text=self.suche, max_preis=self.max_preis, min_rabatt=self.min_rabatt,
                      zustaende=set(self.zustaende), ohne_verdacht=True, ohne_veraltet=True)

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
    """Versionierter lokaler Speicher mit atomarem Schreiben und Fail-Closed-Lesen."""

    def __init__(self, pfad: pathlib.Path | str, missionen: list[Mission] | None = None):
        self.pfad = pathlib.Path(pfad)
        self._lock = threading.RLock()
        self._missionen = list(missionen or [])
        self._pruefe_gesamt(self._missionen)

    @classmethod
    def laden(cls, pfad: pathlib.Path | str) -> "Missionsspeicher":
        datei = pathlib.Path(pfad)
        if datei.is_symlink() or any(p.is_symlink() for p in datei.parents):
            raise MissionsFehler("Symbolische Links im Missionspfad sind nicht erlaubt")
        if not datei.exists():
            return cls(datei)
        try:
            daten = json.loads(datei.read_text(encoding="utf-8"))
            if (not isinstance(daten, dict) or daten.get("version") != FORMAT_VERSION
                    or not isinstance(daten.get("missionen"), list)):
                raise MissionsFehler("Unbekanntes Missionsdateiformat")
            return cls(datei, [Mission.aus_dict(x) for x in daten["missionen"]])
        except MissionsFehler as exc:
            raise MissionsFehler(f"{datei.name}: {exc}") from exc
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise MissionsFehler(f"{datei.name} ist beschädigt und wird nicht überschrieben") from exc

    @contextmanager
    def _dateisperre(self):
        """Exklusive Dateisperre für alle Instanzen/Prozesse desselben Pfads.

        Die Lock-Datei wird nicht ausgetauscht: flock muss auf einer stabilen
        Inode wirken. Manipulierte Links und unsichere Lock-Dateien scheitern.
        """
        if os.name != "posix":
            raise MissionsFehler("Sichere parallele Missionsspeicherung benötigt POSIX")
        import fcntl
        pfad = self.pfad.absolute()
        if pfad.is_symlink() or any(p.is_symlink() for p in pfad.parents):
            raise MissionsFehler("Symbolische Links im Missionspfad sind nicht erlaubt")
        pfad.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
        try:
            fd = os.open(str(pfad) + ".lock", flags, 0o600)
        except OSError as exc:
            raise MissionsFehler("Missionssperre konnte nicht sicher geöffnet werden") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o077:
                raise MissionsFehler("Missionssperre ist nicht privat oder regulär")
            fcntl.flock(fd, fcntl.LOCK_EX)
            if pfad.is_symlink() or any(p.is_symlink() for p in pfad.parents):
                raise MissionsFehler("Missionspfad wurde verändert")
            yield
        finally:
            os.close(fd)

    def _auffrischen(self):
        # Nur unter _dateisperre aufrufen. Ein zweites geladenes Objekt kann
        # inzwischen Änderungen geschrieben haben: nie die alte Kopie nutzen.
        return list(type(self).laden(self.pfad)._missionen)

    @staticmethod
    def _pruefe_gesamt(missionen: list[Mission]) -> None:
        if len(missionen) > MAX_MISSIONEN:
            raise MissionsFehler(f"Höchstens {MAX_MISSIONEN} Missionen")
        ids = [m.id for m in missionen]
        if len(ids) != len(set(ids)):
            raise MissionsFehler("Missions-IDs müssen eindeutig sein")

    def alle(self) -> tuple[Mission, ...]:
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            return tuple(self._missionen)

    def faellige(self, jetzt=None) -> tuple[Mission, ...]:
        zeit = _zeit(jetzt)
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            return tuple(m for m in self._missionen if m.ist_faellig(zeit))

    def _speichern(self, missionen: list[Mission]) -> None:
        if self.pfad.is_symlink() or any(p.is_symlink() for p in self.pfad.absolute().parents):
            raise MissionsFehler("Missionspfad ist ein symbolischer Link")
        self._pruefe_gesamt(missionen)
        inhalt = json.dumps({"version": FORMAT_VERSION,
                             "missionen": [m.als_dict() for m in missionen]},
                            ensure_ascii=False, separators=(",", ":"))
        self.pfad.parent.mkdir(parents=True, exist_ok=True)
        fd, temporaer = tempfile.mkstemp(prefix=".missionen-", suffix=".json", dir=self.pfad.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as datei:
                datei.write(inhalt)
                datei.flush()
                os.fsync(datei.fileno())
            os.replace(temporaer, self.pfad)
        except BaseException:
            pathlib.Path(temporaer).unlink(missing_ok=True)
            raise

    def _ersetzen(self, neu: list[Mission]) -> None:
        self._pruefe_gesamt(neu)
        if self.pfad is not None:
            self._speichern(neu)
        self._missionen = neu

    def erstellen(self, **daten) -> Mission:
        mission = Mission.erstellen(**daten)
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            self._ersetzen([*self._missionen, mission])
        return mission

    def bearbeiten(self, mission_id: str, **daten) -> Mission:
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            index = next((i for i, m in enumerate(self._missionen) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = self._missionen[index]
            neu = Mission.erstellen(
                name=daten.get("name", alt.name), suche=daten.get("suche", alt.suche),
                max_preis=daten.get("max_preis", alt.max_preis),
                min_rabatt=daten.get("min_rabatt", alt.min_rabatt),
                zustaende=daten.get("zustaende", alt.zustaende),
                intervall_minuten=daten.get("intervall_minuten", alt.intervall_minuten),
                jetzt=alt.erstellt_am, mission_id=alt.id)
            neu = Mission(**{**neu.__dict__, "status": alt.status, "letzter_lauf_am": alt.letzter_lauf_am})
            liste = list(self._missionen)
            liste[index] = neu
            self._ersetzen(liste)
            return neu

    def _status(self, mission_id: str, status: str) -> Mission:
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            index = next((i for i, m in enumerate(self._missionen) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = self._missionen[index]
            if alt.status == "beendet" and status != "beendet":
                raise MissionsFehler("Beendete Missionen können nicht reaktiviert werden")
            neu = Mission(**{**alt.__dict__, "status": status})
            liste = list(self._missionen)
            liste[index] = neu
            self._ersetzen(liste)
            return neu

    def pausieren(self, mission_id: str) -> Mission:
        return self._status(mission_id, "pausiert")

    def fortsetzen(self, mission_id: str) -> Mission:
        return self._status(mission_id, "aktiv")

    def beenden(self, mission_id: str) -> Mission:
        return self._status(mission_id, "beendet")

    def lauf_abschliessen(self, mission_id: str, jetzt=None) -> Mission:
        zeit = _zeit(jetzt)
        with self._lock, self._dateisperre():
            self._missionen = self._auffrischen()
            index = next((i for i, m in enumerate(self._missionen) if m.id == mission_id), None)
            if index is None:
                raise MissionsFehler("Mission nicht gefunden")
            alt = self._missionen[index]
            if not alt.ist_faellig(zeit):
                raise MissionsFehler("Mission ist nicht aktiv oder noch nicht fällig")
            neu = Mission(**{**alt.__dict__, "letzter_lauf_am": zeit})
            liste = list(self._missionen)
            liste[index] = neu
            self._ersetzen(liste)
            return neu
