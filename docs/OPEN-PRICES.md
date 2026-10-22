# Echte Ladenpreise: Open Prices (Quelle Q5)

Stand 22.10.2026 · Status: **programmiert und offline getestet, noch nie live abgerufen** (diese Arbeitsumgebung darf
prices.openfoodfacts.org nicht erreichen).

## Was es ist
[Open Prices](https://prices.openfoodfacts.org) ist ein Projekt von Open Food Facts: Menschen melden Preise, die sie
im Laden gesehen haben, mit Barcode, Datum und Geschäft. Kostenlos, ohne Konto, ohne Schlüssel.
Gut für **Lebensmittel und Drogerie** – nicht für Gebrauchtware oder Elektronik.

## Rechte (Prüfung 22.10.2026, keine Rechtsberatung)
- Lizenz **ODbL**. Zwei Bedingungen: **Quelle nennen** und **Weitergabe unter gleichen Bedingungen** –
  wer die Daten mit anderen zu einer neuen Datenbank verbindet, muss diese ebenfalls offen veröffentlichen.
  Beleg: [Open Food Facts – Bedingungen der API](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api)
- Pflicht: eigener User-Agent → `SCHNAPPER/0.1 (…)`.
- **Folge für einen späteren Verkauf:** SCHNAPPER zeigt Open-Prices-Preise nur an und speichert sie nicht dauerhaft.
  Eine eigene Preisdatenbank, die Open-Prices-Daten enthält, müsste offen veröffentlicht werden.

## Schutzmaßnahmen im Code (`app/schnapper/openprices.py`)
- Im Quellen-Register **„später“**; erst `SCHNAPPER_OPENPRICES_FREIGABE=ja` gibt genau diese Quelle frei (nie eine ausgeschlossene).
- Nur `https://prices.openfoodfacts.org`, keine Weiterleitungen, Zeitlimit 15 s, Antwort höchstens 2 MB, höchstens 50 Preise.
- Nur Euro-Stückpreise zum gesuchten Barcode; Dubletten, Kilo-Preise und kaputte Einträge werden übersprungen und gemeldet.
- Jeder Treffer: Link auf den Original-Preis, Beobachtungsdatum (älter als 24 h ⇒ „veraltet“), Lizenzhinweis.
- Rabatt nur, wenn Open Prices selbst einen höheren Normalpreis meldet – sonst „Ersparnis nicht belegbar“.

## Ausprobieren (auf deinem Rechner/Handy mit Internet)
```sh
SCHNAPPER_OPENPRICES_FREIGABE=ja PYTHONPATH=app python -m schnapper --openprices <BARCODE-VOM-PRODUKT> --tage 90 --sortierung preis
```
Ohne Schalter: Meldung „Freigabeschalter … fehlt“, kein Netzwerkaufruf.

Tests: `tests/test_openprices.py` (19 Fälle, ohne Netz, Antwortstruktur laut
[API-Dokumentation](https://openfoodfacts.github.io/documentation/docs/Open-prices/prices/prices_list/)).
