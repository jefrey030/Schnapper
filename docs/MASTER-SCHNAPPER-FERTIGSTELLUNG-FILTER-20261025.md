# SCHNAPPER – Fertigstellungs-Master: Quellen-, Kategorie- und Preisalarmfilter

**Datum:** 25.10.2026 · **Repository:** `jefrey030/Schnapper` · **Branch:** `integration/schnapper-p0-mainbased-20261025` · **Review:** [Draft #55](https://github.com/jefrey030/Schnapper/pull/55) · **Budget:** 0 € zusätzlich.

## Ziel
Vorhandene Suchmöglichkeiten des lokalen SCHNAPPER-App-Kerns vollständig in der Weboberfläche verfügbar machen, ohne fremde oder noch nicht genehmigte Datenquellen zu aktivieren.

## Ausgangsbefund (Codeprüfung)
- `app/schnapper/suche.py::Filter` unterstützt `quellen` und `kategorie` bereits.
- `app/schnapper/web.py::filter_aus_query` übernimmt nur Text, Preis, Rabatt, Zustand und Warnungsfilter. Deshalb ignoriert die Websuche bisher Quellen- und Kategorieparameter.
- `index.html` bietet keine eigenen Quelle-/Kategorie-Felder.
- `app.js` verwendet `FormData` automatisch für Suche und Download, aber `aktuellerWunsch`/`alarmQuery` berücksichtigen neue Filter beim Anlegen/Wiederprüfen von Preisalarmen nicht.
- Die CSV-/JSON-Exporte funktionieren im letzten Master bereits und sollen exakt die gleiche neue Filterlogik nutzen.

## Arbeitsaufträge und Prüfnachweise
| Nr. | Funktion | Erfolgskriterium |
| --- | --- | --- |
| M1 | Backend unterstützt Kategorie | Case-insensitive exakter Kategorievergleich, kein stilles Ignorieren |
| M2 | Backend unterstützt Quelle | Nur Angebote der erlaubten Quelle aus aktuellen geladenen Daten |
| M3 | Suchfilter gegen überlange Eingaben härten | Kontrolliertes HTTP 400 auch in Export statt Fehler 500 |
| M4 | Handy-/Desktop-Webformular erweitern | Zwei sichtbare, zugängliche Felder, ohne gebrochene bestehende Controls |
| M5 | Preisalarme integrieren | Neue Alarme speichern und filtern Kategorie und Quelle korrekt |
| M6 | CSV-/JSON-Export angleichen | Parität von Treffern, Reihenfolge und Quellenschutz mit /api/suche |
| M7 | End-to-End testen | Lokale HTTP-Tests für eigene, mock- und ausgeschlossene Testquellen, Nulltreffer, Kombination, Exporte |
| M8 | Kosten und Sicherheit | Kein Scraping, keine Bezahl-API, keine KI-/Cloud-/Live-Dienste, kein Merge/Deployment |
| M9 | Abschluss dokumentieren | Exakte letzte Commit-SHA, GitHub Actions Python-/Cloudflare-Tests, Restblocker |

## Arbeitsrollen und Grenzen
LEAD ermittelt Iststand; BRAIN implementiert die fehlende Verbindung; CHECK prüft lokale HTTP-Antworten und Formular-/Alarmsteuerung; COMMAND dokumentiert die überprüften Resultate. Das ist die Aufgabenverteilung dieses Masters, **kein Beleg für vier autonome KI-Systeme**.

Weder `main` noch bestehende GitHub-Actions-Crons, eBay-/Open-Prices-Freigaben, Cloudflare-Ressourcen, Preisalarme außerhalb des eigenen Browsers oder echte Nutzer-Daten werden verändert. Der PR bleibt Draft. Weiter offen bleiben externe Datenrechte, tatsächliche Android-Abnahme, unabhängige Sicherheitsreview, Produktiv-Hosting, echte vier KI-Agenten und Betreiberfreigabe.

## Abnahme
### Tatsächlich erledigte Arbeitsblöcke

- [x] **M1 Kategorie:** `app/schnapper/web.py::filter_aus_query` überträgt `kategorie` an den schon vorhandenen Suchkern und filtert Angebote exakt, ohne Groß-/Kleinschreibungsunterschiede.
- [x] **M2 Quelle:** `quelle` wird in `Filter.quellen` übergeben. Der Import überprüft weiterhin die Zulässigkeit jeder Quelle; ausgeschlossene `kleinanzeigen`-Daten gelangen nicht in den Suchbestand.
- [x] **M3 Eingabegrenze:** Beide neuen Parameter werden mit maximal 80 Zeichen begrenzt. Bei zu langen Angaben antwortet die Such- und Export-HTTP-API mit 400 und einer Fehlermeldung.
- [x] **M4 Browserfelder:** `app/schnapper/web/index.html` besitzt zwei beschriftete Felder `quelle` und `kategorie`. Die bestehenden Such- und Exportlinks lesen sie automatisch via `FormData`.
- [x] **M5 Preisalarme:** `app/schnapper/web/app.js` übernimmt beide Felder in `aktuellerWunsch`, die lokale Speicherung, die Alarmbeschreibung und `alarmQuery`; ältere Alarme ohne diese Felder bleiben nutzbar.
- [x] **M6 Exportparität:** Die Routen `/api/export.csv` und `/api/export.json` verwenden schon dieselbe `filter_aus_query`-Prüfung wie `/api/suche`, jetzt einschließlich Quelle und Kategorie.
- [x] **M7 End-to-End-Abnahme:** Neun neue `unittest`-Methoden in `tests/test_fertigstellung_filter.py`, darunter echte lokale HTTP-Anfragen, kombinierte Filter, Verbot unfreigegebener Quellen, Leerergebnisse, CSV-/JSON-Parität, 400-Grenzwerte und Browser-/JS-Prüfungen. **Kein echter Android-Browser-Test**.
- [x] **M8 Kosten/Sicherheit:** Keine externen Datenquellen, kein Scraping, keine Bezahl-API, keine neue Cloud-/KI-Inferenz, kein Deployment. Tests laufen über `127.0.0.1`.
- [x] **M9 Dokumentation:** README und dieser Master aktualisiert; Nachweise und verbleibende Freigaben dokumentiert.

### Reale GitHub-Tests

Code-HEAD `e95732b8087dbf829bbd66fd76b493537d36adbb` hat in [GitHub Actions #40228336361](https://github.com/jefrey030/Schnapper/actions/runs/40228336361) folgende Ergebnisse:
- `python-tests`: **319 Tests ausgeführt, 1 übersprungen, 0 Fehler** – Job `success`.
- `cloudflare-tests`: **16 von 16 bestanden, 0 übersprungen, 0 Fehler** – Job `success`.

**Wichtig:** Nach diesem Code-Stand werden README und der Master als Dokumentationscommits aktualisiert. Der abschließende PR-HEAD wird gesondert durch GitHub Actions geprüft; bis dahin gilt der obige Lauf als Nachweis für die eigentliche Codeänderung, nicht automatisch für nachfolgende Dokumentationscommits.

### Vor Produktivfreigabe weiterhin offen

- Eine rechtmäßig freigegebene, kostenfreie und belastbare Live-Angebotsquelle; die automatische Angebotsrecherche von eBay/Kleinanzeigen ist **nicht** implementiert/freigeschaltet.
- Echte Android-Gerätetests für Touch, Browser-Downloads, Hintergrundverhalten und gespeicherte Alarme.
- Unabhängiges Sicherheitsreview, Produktiv-/Staging-/Kostenprüfung, Monitoring und Betreiberfreigabe.
- Vier tatsächliche autonom laufende KI-Prozesse mit nachgewiesenem stündlichem Betrieb und Not-Aus, nicht nur Code/Mocks.
- `main` enthält weiterhin den alten Stundenworkflow, bis ein **separat freigegebener** Merge erfolgt.

**Ergebnis:** Der kostenlose **Offline-MVP** wurde bei Suche, Export und Preisalarm funktional erweitert. **Vollständige Live-App und Produktionsfreigabe: NO-GO.** Keine erfundenen Prozente oder Livebelege.
