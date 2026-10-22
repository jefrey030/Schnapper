"""Preisverlauf: jeden gesehenen Preis eines Angebots über die Zeit festhalten.

Zweck:
- echte Tiefstpreise erkennen ("so günstig war es in den letzten 30 Tagen nie"),
- Preisänderungen seit dem letzten Mal zeigen,
- geschönte "Statt"-Preise entlarven: Liegt der angegebene Referenzpreis deutlich
  über allem, was SCHNAPPER für dieses Angebot je gesehen hat, wird gewarnt.

Ein Angebot wird über seine bereinigte URL wiedererkannt (ohne Tracking-Parameter).
Gespeichert werden nur URL, Zeitpunkt der Erfassung und Gesamtpreis – keine
Personendaten. Die Datei liegt lokal; nichts wird hochgeladen.

Dateiformat (JSON):
    {"version": 1, "angebote": {"https://...": [["2026-10-21T20:00:00+00:00", "54.89"], ...]}}
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import tempfile
import threading
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from .angebot import Angebot, normalisiere_url

VERSION = 1
MAX_PUNKTE = 200          # je Angebot, die ältesten fallen weg
MAX_ANGEBOTE = 20000      # insgesamt, am längsten nicht gesehene fallen weg
FENSTER_TAGE = 30
MIN_PUNKTE_PRUEFUNG = 3   # so viele Beobachtungen braucht ein Urteil über den Referenzpreis
MIN_TAGE_PRUEFUNG = 7     # ... über mindestens so viele Tage verteilt
REFERENZ_TOLERANZ = Decimal("1.20")  # Referenzpreis darf 20 % über dem Höchstpreis liegen


class VerlaufFehler(ValueError):
    """Verlaufsdatei ist beschädigt. Sie wird dann NICHT überschrieben."""


@dataclass(frozen=True)
class Preisinfo:
    anzahl: int                      # Beobachtungen im Zeitfenster
    tiefst: Decimal
    hoechst: Decimal
    seit_tagen: int                  # wie weit die Beobachtungen zurückreichen
    vorher: Decimal | None           # Preis bei der letzten Beobachtung davor, falls anders
    ist_tiefstpreis: bool
    referenz_fragwuerdig: bool

    def als_dict(self) -> dict:
        return {"anzahl": self.anzahl, "tiefst": str(self.tiefst), "hoechst": str(self.hoechst),
                "seit_tagen": self.seit_tagen, "vorher": None if self.vorher is None else str(self.vorher),
                "ist_tiefstpreis": self.ist_tiefstpreis, "referenz_fragwuerdig": self.referenz_fragwuerdig}


def _zeit(text: str) -> dt.datetime:
    z = dt.datetime.fromisoformat(text)
    return z if z.tzinfo else z.replace(tzinfo=dt.timezone.utc)


class Verlauf:
    def __init__(self, pfad: pathlib.Path | str | None = None):
        self.pfad = None if pfad is None else pathlib.Path(pfad)
        self._lock = threading.RLock()  # Import + Persistenz atomar unter einer Sperre
        self._daten: dict[str, list[tuple[dt.datetime, Decimal]]] = {}

    # ---------- Laden und Speichern ----------
    @classmethod
    def laden(cls, pfad) -> "Verlauf":
        v = cls(pfad)
        if v.pfad is None or not v.pfad.exists():
            return v
        try:
            roh = json.loads(v.pfad.read_text(encoding="utf-8"))
            if not isinstance(roh, dict) or roh.get("version") != VERSION or not isinstance(roh.get("angebote"), dict):
                raise VerlaufFehler("unbekanntes Format")
            for schluessel, punkte in roh["angebote"].items():
                liste = []
                for zeit, preis in punkte:
                    betrag = Decimal(str(preis))
                    if not betrag.is_finite() or betrag <= 0:
                        raise VerlaufFehler(f"ungültiger Preis bei {schluessel}")
                    liste.append((_zeit(zeit), betrag))
                liste.sort(key=lambda p: p[0])
                v._daten[str(schluessel)] = liste[-MAX_PUNKTE:]
        except VerlaufFehler as exc:
            raise VerlaufFehler(f"{v.pfad.name}: {exc}") from exc
        except (ValueError, TypeError, InvalidOperation, json.JSONDecodeError) as exc:
            raise VerlaufFehler(f"{v.pfad.name} ist beschädigt und wird nicht überschrieben ({exc})") from exc
        return v

    def speichern(self) -> None:
        """Atomar schreiben: erst Hilfsdatei, dann umbenennen – nie halb geschriebene Dateien."""
        if self.pfad is None:
            return
        with self._lock:
            inhalt = {"version": VERSION, "angebote": {
                k: [[z.isoformat(), str(p)] for z, p in punkte] for k, punkte in sorted(self._daten.items())}}
        self.pfad.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".verlauf-", suffix=".json", dir=self.pfad.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(inhalt, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, self.pfad)
        except BaseException:
            pathlib.Path(tmp).unlink(missing_ok=True)
            raise

    def importiere(self, angebote: list[Angebot]) -> int:
        """Preise erst nach erfolgreicher Speicherung übernehmen (Rollback bei Fehler).

        RLock hält gleichzeitige Leser fern, während ein Import vorbereitet,
        atomar gespeichert und im Fehlerfall zurückgesetzt wird.
        """
        with self._lock:
            vor_import = {url: list(punkte) for url, punkte in self._daten.items()}
            try:
                neu = self.aufzeichnen(angebote)
                # Auch bei 0 neuen Punkten schreiben: ein vorheriger
                # Schreibfehler darf einen erneuten Versuch nicht unterdrücken.
                self.speichern()
            except BaseException:
                self._daten = vor_import
                raise
            return neu

    # ---------- Aufzeichnen ----------
    def aufzeichnen(self, angebote: list[Angebot]) -> int:
        """Übernimmt die Preise; dieselbe Beobachtung (gleiche URL + gleiche Zeit) zählt nur einmal.

        Gibt die Zahl neu aufgenommener Beobachtungen zurück.
        """
        neu = 0
        with self._lock:
            for a in angebote:
                schluessel = normalisiere_url(a.url)
                punkte = self._daten.setdefault(schluessel, [])
                if any(z == a.erfasst_am for z, _ in punkte):
                    continue
                punkte.append((a.erfasst_am, a.gesamtpreis))
                punkte.sort(key=lambda p: p[0])
                del punkte[:-MAX_PUNKTE]
                neu += 1
            if len(self._daten) > MAX_ANGEBOTE:
                nach_alter = sorted(self._daten, key=lambda k: self._daten[k][-1][0])
                for k in nach_alter[:len(self._daten) - MAX_ANGEBOTE]:
                    del self._daten[k]
        return neu

    def __len__(self) -> int:
        return len(self._daten)

    # ---------- Auswerten ----------
    def info(self, angebot: Angebot, tage: int = FENSTER_TAGE) -> Preisinfo | None:
        """Preisinfo bezogen auf den Zeitpunkt, zu dem das Angebot erfasst wurde."""
        with self._lock:
            punkte = list(self._daten.get(normalisiere_url(angebot.url), ()))
        bis = angebot.erfasst_am
        von = bis - dt.timedelta(days=tage)
        fenster = [(z, p) for z, p in punkte if von <= z <= bis]
        if not any(z == bis for z, _ in fenster):
            fenster.append((bis, angebot.gesamtpreis))
            fenster.sort(key=lambda p: p[0])
        if len(fenster) < 2:
            return None
        aktuell = angebot.gesamtpreis
        preise = [p for _, p in fenster]
        tiefst, hoechst = min(preise), max(preise)
        spanne = fenster[-1][0] - fenster[0][0]
        letzter_davor = next((p for z, p in reversed(fenster) if z < bis), None)
        vorher = None if letzter_davor == aktuell else letzter_davor
        referenz_fragwuerdig = bool(
            angebot.referenzpreis is not None and len(fenster) >= MIN_PUNKTE_PRUEFUNG
            and spanne >= dt.timedelta(days=MIN_TAGE_PRUEFUNG)
            and angebot.referenzpreis > hoechst * REFERENZ_TOLERANZ)
        return Preisinfo(
            anzahl=len(fenster), tiefst=tiefst, hoechst=hoechst, seit_tagen=spanne.days, vorher=vorher,
            ist_tiefstpreis=aktuell <= tiefst and tiefst < hoechst and spanne >= dt.timedelta(days=1),
            referenz_fragwuerdig=referenz_fragwuerdig)


def warnung(info: Preisinfo | None) -> str | None:
    """Text im Stil von angebot.warnungen(), damit Oberfläche und Kommandozeile ihn zeigen."""
    if info is None or not info.referenz_fragwuerdig:
        return None
    return (f"referenzpreis fragwürdig: in {info.seit_tagen} Tagen nie über "
            f"{str(info.hoechst).replace('.', ',')} € gesehen")
