# Echte Ladenpreise: Open Prices (Quelle Q5)

Stand 22.10.2026 · Status: **programmiert und offline getestet, noch nie live abgerufen** (diese Arbeitsumgebung darf
prices.openfoodfacts.org nicht erreichen).

## Was es ist
[Open Prices](https://prices.openfoodfacts.org) ist ein Projekt von Open Food Facts: Menschen melden Preise, die sie
im Laden gesehen haben, mit Barcode, Datum und Geschäft. Kostenlos, ohne Konto, ohne Schlüssel.
Gut für **Lebensmittel und Drogerie** – nicht für Gebrauchtware oder Elektronik.

## Rechte (Prüfung 22.10.2026, keine Rechtsberatung)
- Lizenz **ODbL**: Quellenangabe bei öffentlicher Nutzung, Lizenzhinweis und Share-Alike
  bei öffentlicher Nutzung einer angepassten/abgeleiteten Open-Prices-Datenbank.
  Ob eine eigene Datenbank rechtlich als „adapted database“ gilt, hängt von der tatsächlichen
  Integration/Nutzung ab und lässt sich nicht allein aus dem Namen der App ableiten.
  Belege: [ODbL-Zusammenfassung](https://opendatacommons.org/licenses/odbl/summary/)
  und [Open Food Facts – API-Datenbedingungen](https://support.openfoodfacts.org/help/en-gb/12-api-data-reuse/94-are-there-conditions-to-use-the-api).
- Pflicht: eigener User-Agent → `SCHNAPPER/0.1 (…)`.
- **Folge für einen späteren Verkauf:** SCHNAPPER zeigt Open-Prices-Preise isoliert an,
  speichert sie nicht dauerhaft und erstellt daraus keine eigene Preisdatenbank.
  Eine künftige öffentliche Datenbank-Aggregation braucht eine gesonderte Lizenzprüfung.

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

Tests: `tests/test_openprices.py` (ursprünglich 19 Fälle, inzwischen um Fehlertests erweitert;
nach den neuen GitHub-Änderungen noch nicht erneut lokal ausgeführt; Antwortstruktur laut
[API-Dokumentation](https://openfoodfacts.github.io/documentation/docs/Open-prices/prices/prices_list/)).

## Auf der lokalen Handy-/Browseroberfläche (neu in PR #15)
- Es gibt nun eine eigene Barcode-Suche mit getrennten Ergebnissen; die eigenen CSV-Angebote bleiben unverändert.
- Ab Werk bleibt die Netzwerkabfrage gesperrt. Ohne `SCHNAPPER_OPENPRICES_FREIGABE=ja` kommt HTTP 403 und **kein Netzwerkaufruf** zustande.
- Für einen ausdrücklich gewünschten lokalen Test den Webserver wie folgt starten (kein externer Dienst wird veröffentlicht):
  ```sh
  SCHNAPPER_OPENPRICES_FREIGABE=ja PYTHONPATH=app python -m schnapper.web app/beispiele/angebote.csv
  ```
  Im Browser `http://127.0.0.1:8765` öffnen, Barcode eingeben und „Ladenpreise suchen“ drücken.
- Die Suche zeigt **höchstens die 50 zuletzt gemeldeten Preise zum Barcode**, nicht garantiert alle Preise oder das deutschlandweit günstigste Angebot.
- Preisbeobachtungen sind nutzergemeldete Momentaufnahmen, keine verifizierten aktuellen Ladenangebote.
- Der HTTP-Endpunkt `POST /api/openprices` ist nur von der lokalen Oberfläche für manuelle Abfragen vorgesehen; der Klick allein hebt die Freigabesperre nicht auf.
