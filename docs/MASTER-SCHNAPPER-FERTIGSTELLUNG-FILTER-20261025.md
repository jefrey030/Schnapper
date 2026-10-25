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
Der vorliegende Master ist erst nach realen Commits und vollständigen GitHub-CI-Tests auf **der finalen HEAD-SHA** als implementiert zu kennzeichnen. Keine erfundenen Fertigstellungsprozente.
