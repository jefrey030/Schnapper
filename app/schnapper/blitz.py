"""Offline BLITZ-Queue: passende neue Angebote einmalig als Meldungen ausgeben.

Die Queue versendet nichts selbst. Aufrufer können die Meldungsobjekte in der
lokalen Oberfläche anzeigen oder an einen ausdrücklich konfigurierten Kanal
übergeben. Identische Wunsch-/Angebots-Paare werden dauerhaft unterdrückt.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
from contextlib import contextmanager
import threading
from dataclasses import dataclass
from decimal import Decimal

from .alarm import Wunsch, pruefe_wuensche
from .angebot import normalisiere_url
from .einlesen import Importergebnis
from .sicherer_speicher import verzeichnis, lesen, schreiben

FORMAT_VERSION = 1
MAX_MELDUNGEN = 20_000
_ID = re.compile(r"^[0-9a-f]{64}$")


class BlitzFehler(ValueError):
    """Die lokale Blitz-Historie ist ungültig oder beschädigt."""


@dataclass(frozen=True)
class Benachrichtigung:
    id: str
    wunsch: str
    angebot_id: str
    titel: str
    gesamtpreis: Decimal
    url: str
    erstellt_am: dt.datetime

    def als_dict(self) -> dict:
        return {"id": self.id, "wunsch": self.wunsch, "angebot_id": self.angebot_id,
                "titel": self.titel, "gesamtpreis": str(self.gesamtpreis),
                "url": self.url, "erstellt_am": self.erstellt_am.isoformat()}


def _zeit(wert) -> dt.datetime:
    if wert is None:
        return dt.datetime.now(dt.timezone.utc)
    if not isinstance(wert, dt.datetime) or wert.tzinfo is None or wert.utcoffset() is None:
        raise BlitzFehler("Benachrichtigungszeit muss eine Zeitzone enthalten")
    return wert.astimezone(dt.timezone.utc)


def _wunsch_id(wunsch: Wunsch) -> str:
    norm = json.dumps({
        "suche": wunsch.suche.casefold().strip(),
        "max_preis": None if wunsch.max_preis is None else str(wunsch.max_preis),
        "min_rabatt": None if wunsch.min_rabatt is None else str(wunsch.min_rabatt),
        "zustaende": sorted(wunsch.zustaende),
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class Blitz:
    """Persistente, mehrfach verwendbare und prozessübergreifend gesperrte Queue."""

    def __init__(self, pfad: pathlib.Path | str | None = None, gesehen: dict[str, str] | None = None):
        self.pfad = None if pfad is None else pathlib.Path(pfad)
        self._lock = threading.RLock()
        self._ordner_fd = None
        self._gesehen = dict(gesehen or {})
        if len(self._gesehen) > MAX_MELDUNGEN:
            raise BlitzFehler(f"Höchstens {MAX_MELDUNGEN} gespeicherte Meldungen")

    @contextmanager
    def _dateisperre(self):
        if self.pfad is None:
            yield
            return
        if os.name != "posix":
            raise BlitzFehler("Sichere BLITZ-Speicherung benötigt POSIX")
        import fcntl
        try:
            with verzeichnis(self.pfad) as (ordner, name):
                fd = os.open(name + ".lock", os.O_RDWR | os.O_CREAT | os.O_CLOEXEC |
                             os.O_NOFOLLOW, 0o600, dir_fd=ordner)
                try:
                    info = os.fstat(fd)
                    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                            or info.st_mode & 0o077):
                        raise BlitzFehler("BLITZ-Sperrdatei ist nicht privat oder regulär")
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    self._ordner_fd = ordner
                    try:
                        yield
                    finally:
                        self._ordner_fd = None
                finally:
                    os.close(fd)
        except OSError as exc:
            raise BlitzFehler("BLITZ-Speicherpfad, Sperre oder Schreibvorgang nicht sicher") from exc

    def _auffrischen(self):
        """Nur innerhalb der Dateisperre: aktuellen Datenträgerstand validieren."""
        if self.pfad is None:
            return dict(self._gesehen)
        try:
            roh = lesen(self._ordner_fd, self.pfad.name)
            if roh is None:
                return {}
            daten = json.loads(roh)
            if (not isinstance(daten, dict) or daten.get("version") != FORMAT_VERSION
                    or not isinstance(daten.get("gesehen"), dict)):
                raise BlitzFehler("Unbekanntes Blitzdateiformat")
            gesehen = daten["gesehen"]
            if (len(gesehen) > MAX_MELDUNGEN or
                    any(not isinstance(k, str) or not _ID.fullmatch(k)
                        or not isinstance(v, str) for k, v in gesehen.items())):
                raise BlitzFehler("Blitz-Historie ist ungültig")
            for value in gesehen.values():
                zeitpunkt = dt.datetime.fromisoformat(value)
                if zeitpunkt.tzinfo is None or zeitpunkt.utcoffset() is None:
                    raise BlitzFehler("Blitz-Zeitstempel braucht eine Zeitzone")
            return gesehen
        except BlitzFehler:
            raise
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            raise BlitzFehler("BLITZ-Historie beschädigt und wird nicht überschrieben") from exc

    @classmethod
    def laden(cls, pfad: pathlib.Path | str) -> "Blitz":
        speicher = cls(pfad)
        with speicher._lock, speicher._dateisperre():
            speicher._gesehen = speicher._auffrischen()
        return speicher

    def _schreiben(self, gesehen: dict[str, str]) -> None:
        if self.pfad is None:
            return
        if self._ordner_fd is None:
            # Auch direkte interne Aufrufe dürfen nie die sicheren FDs umgehen.
            with self._lock, self._dateisperre():
                self._schreiben(gesehen)
            return
        inhalt = json.dumps({"version": FORMAT_VERSION, "gesehen": gesehen},
                            ensure_ascii=False, separators=(",", ":"))
        schreiben(self._ordner_fd, self.pfad.name, inhalt)

    def pruefen(self, geladen: Importergebnis, wuensche: list[Wunsch],
                jetzt: dt.datetime | None = None) -> list[Benachrichtigung]:
        zeit = _zeit(jetzt)
        with self._lock, self._dateisperre():
            # Load-under-lock verhindert doppelte BLITZ-Meldungen nach einem Neustart
            # oder durch eine zweite, zuvor geladene Instanz.
            if self.pfad is not None:
                self._gesehen = self._auffrischen()
            neu_gesehen = dict(self._gesehen)
            meldungen = []
            for alarm in pruefe_wuensche(geladen, wuensche, jetzt=zeit):
                wunsch_key = _wunsch_id(alarm.wunsch)
                for treffer in alarm.treffer:
                    angebot = treffer.angebot
                    schluessel = hashlib.sha256(
                        f"{wunsch_key}\0{normalisiere_url(angebot.url)}".encode("utf-8")).hexdigest()
                    if schluessel in neu_gesehen:
                        continue
                    neu_gesehen[schluessel] = zeit.isoformat()
                    meldungen.append(Benachrichtigung(
                        id=schluessel, wunsch=alarm.wunsch.name, angebot_id=angebot.id,
                        titel=angebot.titel, gesamtpreis=angebot.gesamtpreis,
                        url=angebot.url, erstellt_am=zeit))
            if len(neu_gesehen) > MAX_MELDUNGEN:
                sortiert = sorted(neu_gesehen.items(), key=lambda eintrag: eintrag[1])
                neu_gesehen = dict(sortiert[-MAX_MELDUNGEN:])
            self._schreiben(neu_gesehen)
            self._gesehen = neu_gesehen
            return meldungen

    def __len__(self) -> int:
        with self._lock, self._dateisperre():
            if self.pfad is not None:
                self._gesehen = self._auffrischen()
            return len(self._gesehen)
