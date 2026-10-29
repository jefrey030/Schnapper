"""Preisalarm (BLITZ): gespeicherte Wünsche gegen eine Angebotsliste prüfen.

Ein Wunsch ist eine gespeicherte Suche mit Schmerzgrenze, z. B.
"Kopfhörer, höchstens 60 € inkl. Versand, gebraucht oder wie neu".
Ausgelöst wird ein Alarm nur von Angeboten, denen man trauen kann:
Betrugsverdacht und veraltete Preise lösen standardmäßig KEINEN Alarm aus.

Wunschliste als JSON:
    {"wuensche": [{"name": "Kopfhörer", "suche": "kopfhoerer", "max_preis": "60",
                   "zustaende": ["gebraucht", "wie_neu"], "min_rabatt": "40"}]}

Aufruf:
    PYTHONPATH=app python -m schnapper.alarm app/beispiele/angebote.csv app/beispiele/wuensche.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from .adapter import finde_in
from .angebot import ZUSTAENDE, AngebotFehler, geld
from .einlesen import Importergebnis, lies_datei
from .suche import Filter, Treffer

MAX_WUENSCHE = 100


class WunschFehler(ValueError):
    """Ein Wunsch ist unvollständig oder unplausibel."""


@dataclass(frozen=True)
class Wunsch:
    name: str
    suche: str
    max_preis: Decimal | None = None
    min_rabatt: Decimal | None = None
    zustaende: frozenset[str] = field(default_factory=frozenset)
    region: str = ""
    entfernung_km: Decimal | None = None

    @classmethod
    def aus_dict(cls, daten: dict) -> "Wunsch":
        if not isinstance(daten, dict):
            raise WunschFehler("Wunsch muss ein Objekt sein")
        suche = str(daten.get("suche") or "").strip()[:200]
        if not suche:
            raise WunschFehler("Feld 'suche' fehlt")
        name = str(daten.get("name") or suche).strip()[:100]
        try:
            max_preis = geld(daten["max_preis"]) if daten.get("max_preis") not in (None, "") else None
        except AngebotFehler as exc:
            raise WunschFehler(f"Höchstpreis nicht lesbar: {daten.get('max_preis')!r}") from exc
        if max_preis is not None and max_preis <= 0:
            raise WunschFehler("Höchstpreis muss größer als 0 sein")
        try:
            roh = daten.get("min_rabatt")
            min_rabatt = None if roh in (None, "") else Decimal(str(roh).replace(",", "."))
        except InvalidOperation as exc:
            raise WunschFehler(f"Mindestrabatt nicht lesbar: {daten.get('min_rabatt')!r}") from exc
        if min_rabatt is not None and (not min_rabatt.is_finite() or not 0 <= min_rabatt <= 100):
            raise WunschFehler("Mindestrabatt muss zwischen 0 und 100 liegen")
        zustaende = daten.get("zustaende")
        if zustaende is None or zustaende == "":
            zustaende = []
        elif isinstance(zustaende, str):
            zustaende = [zustaende]
        if not isinstance(zustaende, (list, tuple, set, frozenset)):
            raise WunschFehler("Zustand muss eine Liste oder Text sein")
        zustaende = frozenset(str(z).strip().lower() for z in zustaende if str(z).strip())
        unbekannt = zustaende - set(ZUSTAENDE)
        if unbekannt:
            raise WunschFehler(f"Unbekannter Zustand: {', '.join(sorted(unbekannt))}")
        if max_preis is None and min_rabatt is None:
            raise WunschFehler("Mindestens Höchstpreis oder Mindestrabatt angeben, sonst ist es kein Alarm")
        region = daten.get("region", "")
        if not isinstance(region, str) or len(region.strip()) > 100:
            raise WunschFehler("Region darf höchstens 100 Zeichen enthalten")
        entfernung = daten.get("entfernung_km")
        if entfernung in (None, ""):
            entfernung = None
        else:
            try:
                entfernung = Decimal(str(entfernung).replace(",", "."))
            except (InvalidOperation, AttributeError) as exc:
                raise WunschFehler("Entfernung ist ungültig") from exc
            if not entfernung.is_finite() or not 0 <= entfernung <= 500:
                raise WunschFehler("Entfernung muss zwischen 0 und 500 km liegen")
        return cls(name=name, suche=suche, max_preis=max_preis, min_rabatt=min_rabatt,
                   zustaende=zustaende, region=region.strip(), entfernung_km=entfernung)

    def als_filter(self, mit_veraltet: bool = False) -> Filter:
        return Filter(text=self.suche, max_preis=self.max_preis, min_rabatt=self.min_rabatt,
                      zustaende=set(self.zustaende), region=self.region,
                      entfernung_km=self.entfernung_km,
                      ohne_verdacht=True, ohne_veraltet=not mit_veraltet)


@dataclass
class Wunschliste:
    wuensche: list[Wunsch] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)


def lies_wuensche(text: str) -> Wunschliste:
    """Fehlerhafte Wünsche werden gemeldet, der Rest wird übernommen."""
    ergebnis = Wunschliste()
    try:
        daten = json.loads(text)
    except json.JSONDecodeError as exc:
        ergebnis.fehler.append(f"Wunschliste: kein gültiges JSON ({exc.msg})")
        return ergebnis
    if isinstance(daten, dict):
        daten = daten.get("wuensche")
    if not isinstance(daten, list):
        ergebnis.fehler.append('Wunschliste muss eine Liste oder {"wuensche": [...]} sein')
        return ergebnis
    if len(daten) > MAX_WUENSCHE:
        ergebnis.fehler.append(f"Mehr als {MAX_WUENSCHE} Wünsche – nur die ersten {MAX_WUENSCHE} werden geprüft")
        daten = daten[:MAX_WUENSCHE]
    for nr, eintrag in enumerate(daten, start=1):
        try:
            ergebnis.wuensche.append(Wunsch.aus_dict(eintrag))
        except WunschFehler as exc:
            ergebnis.fehler.append(f"Wunsch {nr}: {exc}")
    return ergebnis


@dataclass(frozen=True)
class Alarm:
    wunsch: Wunsch
    treffer: tuple[Treffer, ...]

    @property
    def bester(self) -> Treffer | None:
        return self.treffer[0] if self.treffer else None


def pruefe_wuensche(geladen: Importergebnis, wuensche: list[Wunsch], jetzt: dt.datetime | None = None,
                    mit_veraltet: bool = False) -> list[Alarm]:
    """Für jeden Wunsch die passenden Angebote, günstigstes zuerst (Dubletten bereits entfernt)."""
    alarme = []
    for w in wuensche:
        ergebnis = finde_in(geladen, w.als_filter(mit_veraltet), "preis", jetzt=jetzt)
        alarme.append(Alarm(w, tuple(ergebnis.treffer)))
    return alarme


def _euro(betrag: Decimal) -> str:
    """59.9 -> '59,90 €' (deutsche Schreibweise)."""
    return f"{betrag:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"


def _wunsch_text(w: Wunsch) -> str:
    teile = [f"„{w.suche}“"]
    if w.max_preis is not None:
        teile.append(f"bis {_euro(w.max_preis)}")
    if w.min_rabatt is not None:
        teile.append(f"ab {str(w.min_rabatt).replace('.', ',')} % billiger")
    if w.zustaende:
        teile.append("/".join(sorted(w.zustaende)))
    return ", ".join(teile)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="schnapper.alarm", description="Preisalarm: Wunschliste gegen Angebote prüfen")
    p.add_argument("angebote", help=".csv/.json mit Angeboten")
    p.add_argument("wuensche", help=".json mit Wünschen")
    p.add_argument("--mit-veraltet", action="store_true", help="auch Preise älter als 24 Std. melden")
    p.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    a = p.parse_args(argv)

    try:
        liste = lies_wuensche(pathlib.Path(a.wuensche).read_text(encoding="utf-8-sig"))
        geladen = lies_datei(a.angebote)
    except OSError as exc:
        print("Datei nicht lesbar:", exc, file=sys.stderr)
        return 1
    alarme = pruefe_wuensche(geladen, liste.wuensche, mit_veraltet=a.mit_veraltet)
    ausgeloest = [x for x in alarme if x.treffer]

    if a.json:
        print(json.dumps({
            "wuensche": len(liste.wuensche), "ausgeloest": len(ausgeloest),
            "fehler": liste.fehler + geladen.fehler,
            "alarme": [{"name": x.wunsch.name, "treffer": [
                {"id": t.angebot.id, "titel": t.angebot.titel, "gesamtpreis": str(t.angebot.gesamtpreis),
                 "rabatt_prozent": None if t.angebot.rabatt_prozent is None else str(t.angebot.rabatt_prozent),
                 "quelle": t.angebot.quelle, "url": t.angebot.url, "warnungen": list(t.warnungen)}
                for t in x.treffer]} for x in alarme],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{len(liste.wuensche)} Wünsche geprüft, {len(ausgeloest)} Alarm(e)")
        for x in alarme:
            if not x.treffer:
                print(f"  –  {x.wunsch.name}: nichts unter der Schmerzgrenze ({_wunsch_text(x.wunsch)})")
                continue
            print(f"  ⚡ {x.wunsch.name}: {len(x.treffer)} Treffer ({_wunsch_text(x.wunsch)})")
            for t in x.treffer:
                r = "" if t.angebot.rabatt_prozent is None else f"  −{str(t.angebot.rabatt_prozent).replace('.', ',')} %"
                print(f"       {_euro(t.angebot.gesamtpreis):>11}{r}  {t.angebot.titel}  [{t.angebot.quelle}]")
                print(f"       {t.angebot.url}")
        for f in liste.fehler + geladen.fehler:
            print("HINWEIS:", f, file=sys.stderr)
    # 0 = mindestens ein Alarm, 3 = keiner (praktisch für Automatisierung), 2 = fehlerhafte Wünsche
    if liste.fehler:
        return 2
    return 0 if ausgeloest else 3


if __name__ == "__main__":
    sys.exit(main())
