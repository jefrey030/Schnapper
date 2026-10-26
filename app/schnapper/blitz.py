"""Offline BLITZ-Queue: passende neue Angebote einmalig als Meldungen ausgeben.

Die Queue versendet nichts selbst. Aufrufer können die Meldungsobjekte in der
lokalen Oberfläche anzeigen oder an einen ausdrücklich konfigurierten Kanal
übergeben. Identische Wunsch-/Angebots-Paare werden dauerhaft unterdrückt.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import threading
from dataclasses import dataclass
from decimal import Decimal

from .alarm import Wunsch, pruefe_wuensche
from .angebot import normalisiere_url
from .einlesen import Importergebnis
from .sicherer_speicher import dateisperre, digest, lese_fd, schreibe_fd

FORMAT_VERSION = 2
MAX_MELDUNGEN = 20_000
_ID = re.compile(r"^[0-9a-f]{64}$")


class BlitzFehler(ValueError):
    """Die lokale Blitz-Historie ist ungültig oder beschädigt."""


class BlitzKonflikt(BlitzFehler):
    """Ein anderer Prozess hat die Deduplizierungshistorie parallel aktualisiert."""


@dataclass(frozen=True)
class Benachrichtigung:
    id: str
    wunsch: str
    angebot_id: str
    titel: str
    gesamtpreis: Decimal
    url: str
    quelle: str
    erstellt_am: dt.datetime

    def als_dict(self) -> dict:
        return {"id": self.id, "wunsch": self.wunsch, "angebot_id": self.angebot_id,
                "titel": self.titel, "gesamtpreis": str(self.gesamtpreis),
                "url": self.url, "quelle": self.quelle,
                "erstellt_am": self.erstellt_am.isoformat()}


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
        "region": wunsch.region,
        "entfernung_km": None if wunsch.entfernung_km is None else str(wunsch.entfernung_km),
    }, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


class Blitz:
    def __init__(self, pfad: pathlib.Path | str | None = None, gesehen: dict[str, str] | None = None,
                 _revision: str | None = None):
        self.pfad = None if pfad is None else pathlib.Path(pfad)
        self._lock = threading.RLock()
        self._gesehen = dict(gesehen or {})
        self._revision = _revision
        if len(self._gesehen) > MAX_MELDUNGEN:
            raise BlitzFehler(f"Höchstens {MAX_MELDUNGEN} gespeicherte Meldungen")

    @classmethod
    def _dekodiere(cls, raw: bytes | None, dateiname: str) -> tuple[dict[str, str], str | None]:
        if raw is None:
            return {}, None
        try:
            daten = json.loads(raw.decode("utf-8"))
            if (not isinstance(daten, dict) or type(daten.get("version")) is not int
                    or daten.get("version") not in (1, FORMAT_VERSION)
                    or not isinstance(daten.get("gesehen"), dict)):
                raise BlitzFehler("Unbekanntes Blitzdateiformat")
            gesehen = daten["gesehen"]
            if (len(gesehen) > MAX_MELDUNGEN or
                    any(not isinstance(k, str) or not _ID.fullmatch(k)
                        or not isinstance(v, str) for k, v in gesehen.items())):
                raise BlitzFehler("Blitz-Historie ist ungültig")
            for zeit in gesehen.values():
                zeitpunkt = dt.datetime.fromisoformat(zeit)
                if zeitpunkt.tzinfo is None or zeitpunkt.utcoffset() is None:
                    raise BlitzFehler("Blitz-Zeitstempel braucht eine Zeitzone")
            return dict(gesehen), digest(raw)
        except BlitzFehler as exc:
            raise BlitzFehler(f"{dateiname}: {exc}") from exc
        except (OSError, ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BlitzFehler(f"{dateiname} ist beschädigt und wird nicht überschrieben") from exc

    @classmethod
    def laden(cls, pfad: pathlib.Path | str) -> "Blitz":
        datei = pathlib.Path(pfad)
        try:
            with dateisperre(datei) as (directory, name):
                gesehen, revision = cls._dekodiere(lese_fd(directory, name), datei.name)
            return cls(datei, gesehen, revision)
        except BlitzFehler:
            raise
        except OSError as exc:
            raise BlitzFehler(f"{datei.name} kann nicht sicher gelesen werden") from exc

    def pruefen(self, geladen: Importergebnis, wuensche: list[Wunsch],
                jetzt: dt.datetime | None = None) -> list[Benachrichtigung]:
        zeit = _zeit(jetzt)
        with self._lock:
            if self.pfad is None:
                neu_gesehen = self._berechne_meldungen(dict(self._gesehen), geladen, wuensche, zeit)
                self._gesehen, meldungen = neu_gesehen
                return meldungen
            try:
                with dateisperre(self.pfad) as (directory, name):
                    aktuell, revision = self._dekodiere(lese_fd(directory, name), self.pfad.name)
                    if revision != self._revision:
                        self._gesehen, self._revision = aktuell, revision
                        raise BlitzKonflikt(
                            "BLITZ-Historie wurde parallel geändert; erneut laden und Treffer neu prüfen")
                    neu_gesehen, meldungen = self._berechne_meldungen(
                        aktuell, geladen, wuensche, zeit)
                    raw = json.dumps(
                        {"version": FORMAT_VERSION, "gesehen": neu_gesehen},
                        ensure_ascii=False, separators=(",", ":"),
                    ).encode("utf-8")
                    schreibe_fd(directory, name, raw)
                    self._gesehen, self._revision = neu_gesehen, digest(raw)
                    return meldungen
            except (BlitzFehler, BlitzKonflikt):
                raise
            except OSError as exc:
                raise BlitzFehler("BLITZ-Historie konnte nicht sicher gespeichert werden") from exc

    @staticmethod
    def _berechne_meldungen(gesehen, geladen, wuensche, zeit):
        neu_gesehen = dict(gesehen)
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
                    url=angebot.url, quelle=angebot.quelle, erstellt_am=zeit))
        if len(neu_gesehen) > MAX_MELDUNGEN:
            sortiert = sorted(neu_gesehen.items(), key=lambda eintrag: eintrag[1])
            neu_gesehen = dict(sortiert[-MAX_MELDUNGEN:])
        return neu_gesehen, meldungen

    def __len__(self) -> int:
        with self._lock:
            if self.pfad is None:
                return len(self._gesehen)
            try:
                with dateisperre(self.pfad) as (directory, name):
                    self._gesehen, self._revision = self._dekodiere(
                        lese_fd(directory, name), self.pfad.name)
                return len(self._gesehen)
            except BlitzFehler:
                raise
            except OSError as exc:
                raise BlitzFehler(f"{self.pfad.name} kann nicht sicher gelesen werden") from exc

    def exportdaten(self) -> dict:
        with self._lock:
            if self.pfad is None:
                return {"version": FORMAT_VERSION, "gesehen": dict(self._gesehen)}
            try:
                with dateisperre(self.pfad) as (directory, name):
                    self._gesehen, self._revision = self._dekodiere(
                        lese_fd(directory, name), self.pfad.name)
                return {"version": FORMAT_VERSION, "gesehen": dict(self._gesehen)}
            except BlitzFehler:
                raise
            except OSError as exc:
                raise BlitzFehler(f"{self.pfad.name} kann nicht sicher gelesen werden") from exc
