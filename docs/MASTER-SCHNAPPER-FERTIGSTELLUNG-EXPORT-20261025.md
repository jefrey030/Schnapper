# SCHNAPPER – großer Fertigstellungs-Master: überprüfbarer Ergebnisexport

**Datum:** 25.10.2026 · **Arbeitszweig:** `integration/schnapper-p0-mainbased-20261025` · **Review:** [PR #55](https://github.com/jefrey030/Schnapper/pull/55) · **Zusatzkosten:** 0 € · **Freigabe:** NO-GO

## Ausgangslage und Ziel

Der lokale Offline-MVP besitzt bereits Suche, CSV-/JSON-Import, Preisvergleich, Warnungen, Dubletten, Preisverlauf und Browserseite. Im aktuellen Draft sind außerdem Links zu `/api/export.csv` und `/api/export.json` sowie eine erste Implementierung vorhanden. Das ist kein vollständig abgenommener Export.

**Dieser Master vollendet und verifiziert den Ergebnisexport.** Nicht erneut bereits vorhandene Funktionen neu erfinden, sondern das vorhandene Feature fachlich vervollständigen, sicher testen und seine Grenzen dokumentieren.

## Funktionale Abnahme

| Paket | Auftrag | Bestanden wenn |
| --- | --- | --- |
| EX1 | Aktuelle Quellcode-Lage und PR-Zustand erheben | SHA, Export-Code, UI-Links und Nachweislücken erfasst |
| EX2 | CSV-/JSON-Export fachlich vervollständigen | Preis, Versand, Referenzpreis und Rabatt aus exakt dem gefilterten/entdoppelten Trefferbestand |
| EX3 | Fremde Texte sicher als CSV exportieren | UTF-8/BOM, Semikolon und CRLF, Spreadsheet-Formel-Escaping, keine rohe Zeileninjektion |
| EX4 | HTTP-Verträge absichern | JSON mit Datenherkunft, CSV-Spalten und Download-Header, HEAD ohne Body |
| EX5 | Fehler und Nulltreffer | identische Filtervalidierung wie `/api/suche`, 400 statt Fehlerseite; leere CSV mit Kopfzeile |
| EX6 | Browser-/Handy-Zugriff | Download-Links vorhanden und an aktive Formfilter gebunden (statische Prüfung; kein echter Android-Test) |
| EX7 | Kein unerlaubtes Netz | kein neuer API-Abruf, kein eBay, kein Cloud-Modell, keine Kosten |
| EX8 | Review-Nachweise | neue Regressionstests plus gesamte Python-/Cloudflare-CI für die finale SHA |
| EX9 | Projekt-Restarbeiten aktualisieren | externe Quellengenehmigung, Security-/Android-/Live-KI-Abnahme explizit weiter offen |

## Vier Arbeitsfunktionen (keine vier laufenden KI-Modelle)

- **LEAD:** vorhandenes Feature und Release-Sperren prüfen.
- **BRAIN:** gezielte Exportkorrektur ohne Produktiv-/Main-Änderungen.
- **CHECK:** reale lokale HTTP-Abnahme und negative Fälle mit `unittest` (keine externen APIs).
- **COMMAND:** Belege mit exakter SHA, CI-Run und verbleibenden Blockern im Draft hinterlegen.

## Sicherheitsgrenzen

- Keine ungeprüften Modellaufrufe, Zahlungen, kostenpflichtigen APIs, Infrastruktur-/Github-Billing-Änderungen, Scraper oder Veröffentlichungen.
- Nur vorhandene, freigegebene lokale Angebote exportieren. Die Quelle `kleinanzeigen` bleibt ausgeschlossen und `ebay` ohne Zulassung gesperrt.
- Keine autonomen, simulierten Rollen als echte Live-Agenten ausgeben.
- Der Entwurf #55 bleibt Draft. `main` und dessen historischer Cron bleiben bis zur ausdrücklichen Freigabe unangetastet.

## Ausführung und Abschluss

Die tatsächlichen Code-Commits, neuen Tests, letzte GitHub-Actions-SHA, PASS/SKIP/FAIL-Zahlen sowie unerledigten externen Freigaben werden **erst nach Prüfung** ergänzt.
