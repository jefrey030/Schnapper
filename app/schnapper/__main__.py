"""Kommandozeile: python -m schnapper DATEI [--suche TEXT] [--max-preis 50] ...

Quellen (genau eine): DATEI, --openprices EAN oder --ebay SUCHBEGRIFF.

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
from .verlauf import Verlauf, VerlaufFehler, warnung


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="schnapper", description="Schnäppchen aus einer Angebotsdatei finden")
    p.add_argument("datei", nargs="?", help=".json oder .csv mit Angeboten")
    p.add_argument("--openprices", metavar="EAN", help="Echte Ladenpreise zu diesem Barcode von Open Prices abrufen "
                   "(nur mit SCHNAPPER_OPENPRICES_FREIGABE=ja)")
    p.add_argument("--ebay", metavar="SUCHBEGRIFF",
                   help="Angebote über die eBay Browse API suchen (Sandbox standardmäßig; nur mit "
                        "SCHNAPPER_EBAY_FREIGABE=ja sowie SCHNAPPER_EBAY_CLIENT_ID und "
                        "SCHNAPPER_EBAY_CLIENT_SECRET; Produktion nur mit SCHNAPPER_EBAY_PRODUKTION=ja)")
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
    p.add_argument("--verlauf", help="Preisverlauf-Datei: Preise festhalten und Tiefstpreise erkennen")
    a = p.parse_args(argv)
    if sum(x is not None for x in (a.datei, a.openprices, a.ebay)) != 1:
        p.error("genau eines angeben: DATEI, --openprices EAN oder --ebay SUCHBEGRIFF")

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
    elif a.ebay is not None:
        from .ebay import HINWEIS_QUELLE, EbayAdapter, EbayFehler, EbayGesperrt
        try:
            adapter = EbayAdapter(a.ebay)
            ergebnis = adapter.lade()
        except (ValueError, EbayGesperrt, EbayFehler) as exc:
            print(f"eBay: {exc}", file=sys.stderr)
            return 3
        for hinweis in adapter.hinweise:
            print(f"eBay-Hinweis: {hinweis}", file=sys.stderr)
        lizenz = HINWEIS_QUELLE
    else:
        ergebnis = lies_datei(a.datei)
    verlauf = None
    if a.verlauf:
        try:
            verlauf = Verlauf.laden(a.verlauf)
        except VerlaufFehler as exc:
            print("Preisverlauf:", exc, file=sys.stderr)
            return 1
        if verlauf.aufzeichnen(ergebnis.angebote):
            verlauf.speichern()
    eindeutig, dubletten = entferne_dubletten(ergebnis.angebote)
    f = Filter(text=a.suche,
               max_preis=geld(a.max_preis) if a.max_preis else None,
               min_rabatt=Decimal(a.min_rabatt) if a.min_rabatt else None,
               zustaende=set(a.zustand), quellen=set(a.quelle),
               ohne_verdacht=not a.mit_verdacht, ohne_veraltet=a.ohne_veraltet)
    treffer = suche(eindeutig, f, a.sortierung)
    infos = {t.angebot.id: verlauf.info(t.angebot) if verlauf else None for t in treffer}

    def alle_warnungen(t):
        return list(t.warnungen) + [w for w in (warnung(infos[t.angebot.id]),) if w]

    if a.json:
        print(json.dumps({
            "eingelesen": len(ergebnis.angebote), "ungueltig": ergebnis.fehler, "lizenz": lizenz,
            "dubletten_entfernt": [{"entfernt": x.id, "behalten": y.id} for x, y in dubletten],
            "treffer": [{"id": t.angebot.id, "titel": t.angebot.titel, "gesamtpreis": str(t.angebot.gesamtpreis),
                         "rabatt_prozent": None if t.angebot.rabatt_prozent is None else str(t.angebot.rabatt_prozent),
                         "quelle": t.angebot.quelle, "url": t.angebot.url, "warnungen": alle_warnungen(t),
                         "verlauf": None if infos[t.angebot.id] is None else infos[t.angebot.id].als_dict()}
                        for t in treffer],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"{len(ergebnis.angebote)} gültig, {len(ergebnis.fehler)} ungültig, "
              f"{len(dubletten)} Dubletten entfernt, {len(treffer)} Treffer")
        for t in treffer:
            r = "  –  " if t.angebot.rabatt_prozent is None else f"{t.angebot.rabatt_prozent:>4}%"
            print(f"{r}  {t.angebot.gesamtpreis:>9} €  {t.angebot.titel}  [{t.angebot.quelle}]")
            info = infos[t.angebot.id]
            if info is not None:
                zeile = f"spanne {info.tiefst}–{info.hoechst} € in {info.seit_tagen} Tagen"
                if info.ist_tiefstpreis:
                    zeile = "TIEFSTPREIS · " + zeile
                if info.vorher is not None:
                    zeile += f" · vorher {info.vorher} €"
                print(f"         ~ {zeile}")
            for w in alle_warnungen(t):
                print(f"         ! {w}")
        for fehler in ergebnis.fehler:
            print("UNGÜLTIG:", fehler, file=sys.stderr)
        if lizenz:
            print(lizenz)
    return 0 if not ergebnis.fehler else 2


if __name__ == "__main__":
    sys.exit(main())
