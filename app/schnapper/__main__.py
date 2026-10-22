"""Kommandozeile: python -m schnapper DATEI [--suche TEXT] [--max-preis 50] ...

Aufruf aus dem Repo-Stamm:  PYTHONPATH=app python -m schnapper beispiele/angebote.json
"""
from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal

from .angebot import geld
from .dubletten import entferne_dubletten
from .einlesen import lies_datei
from .suche import SORTIERUNGEN, Filter, suche


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="schnapper", description="Schnäppchen aus einer Angebotsdatei finden")
    p.add_argument("datei", nargs="?", help=".json oder .csv mit Angeboten")
    p.add_argument("--openprices", metavar="EAN", help="Echte Ladenpreise zu diesem Barcode von Open Prices abrufen "
                   "(nur mit SCHNAPPER_OPENPRICES_FREIGABE=ja)")
    p.add_argument("--tage", type=int, default=90, help="Zeitraum für --openprices in Tagen")
    p.add_argument("--suche", default="", help="Suchwörter, alle müssen im Titel vorkommen")
    p.add_argument("--max-preis", help="Höchster Gesamtpreis inkl. Versand")
    p.add_argument("--min-rabatt", help="Mindestersparnis in Prozent")
    p.add_argument("--zustand", action="append", default=[], help="neu, wie_neu, gebraucht, defekt")
    p.add_argument("--quelle", action="append", default=[])
    p.add_argument("--sortierung", choices=SORTIERUNGEN, default="rabatt")
    p.add_argument("--ohne-veraltet", action="store_true", help="Preise älter als 24 Std. ausblenden")
    p.add_argument("--mit-verdacht", action="store_true", help="Betrugsverdacht nicht ausblenden")
    p.add_argument("--json", action="store_true", help="Ausgabe als JSON")
    a = p.parse_args(argv)
    if bool(a.datei) == bool(a.openprices):
        p.error("entweder DATEI oder --openprices EAN angeben")

    lizenz = None
    if a.openprices:
        from .openprices import LIZENZ, OpenPricesAdapter, OpenPricesFehler, OpenPricesGesperrt
        try:
            adapter = OpenPricesAdapter(a.openprices, a.tage)
            ergebnis = adapter.lade()
        except (ValueError, OpenPricesGesperrt, OpenPricesFehler) as exc:
            print(f"Open Prices: {exc}", file=sys.stderr)
            return 3
        lizenz = LIZENZ
    else:
        ergebnis = lies_datei(a.datei)
    eindeutig, dubletten = entferne_dubletten(ergebnis.angebote)
    f = Filter(text=a.suche,
               max_preis=geld(a.max_preis) if a.max_preis else None,
               min_rabatt=Decimal(a.min_rabatt) if a.min_rabatt else None,
               zustaende=set(a.zustand), quellen=set(a.quelle),
               ohne_verdacht=not a.mit_verdacht, ohne_veraltet=a.ohne_veraltet)
    treffer = suche(eindeutig, f, a.sortierung)

    if a.json:
        print(json.dumps({
            "eingelesen": len(ergebnis.angebote), "ungueltig": ergebnis.fehler, "lizenz": lizenz,
            "dubletten_entfernt": [{"entfernt": x.id, "behalten": y.id} for x, y in dubletten],
            "treffer": [{"id": t.angebot.id, "titel": t.angebot.titel, "gesamtpreis": str(t.angebot.gesamtpreis),
                         "rabatt_prozent": None if t.angebot.rabatt_prozent is None else str(t.angebot.rabatt_prozent),
                         "quelle": t.angebot.quelle, "url": t.angebot.url, "warnungen": list(t.warnungen)}
                        for t in treffer],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{len(ergebnis.angebote)} gültig, {len(ergebnis.fehler)} ungültig, "
              f"{len(dubletten)} Dubletten entfernt, {len(treffer)} Treffer")
        for t in treffer:
            r = "  –  " if t.angebot.rabatt_prozent is None else f"{t.angebot.rabatt_prozent:>4}%"
            print(f"{r}  {t.angebot.gesamtpreis:>9} €  {t.angebot.titel}  [{t.angebot.quelle}]")
            for w in t.warnungen:
                print(f"         ! {w}")
        for fehler in ergebnis.fehler:
            print("UNGÜLTIG:", fehler, file=sys.stderr)
        if lizenz:
            print(lizenz)
    return 0 if not ergebnis.fehler else 2


if __name__ == "__main__":
    sys.exit(main())
