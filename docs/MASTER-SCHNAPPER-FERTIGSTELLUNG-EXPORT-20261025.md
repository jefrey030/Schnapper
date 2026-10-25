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

## Tatsächlich ausgeführt und geprüft

**EX1 – Ausgangslage und bestehendes Feature:** Zu Beginn war die Export-Route bereits als erster Entwurf implementiert, aber ohne gezielte vollständige Regressionstests und ohne `referenzpreis` als CSV-Spalte. Bestehende UI-Links im Browser wurden weiterverwendet statt neu angelegt.

**EX2 – fachliche CSV-Verbesserung:** `app/schnapper/web.py`: Die CSV enthält neu die Spalte `referenzpreis` als Teil von `CSV_FELDER`. Getestet werden preislich gefilterte Treffer mit `gesamtpreis`, `preis`, `versand`, `referenzpreis`, `rabatt_prozent` und Quellennachweis. Eine normale, vertrauenswürdige Eigenliste kann im Test wieder als CSV eingelesen werden.

**EX3 – Sicherheit:** Tabulatoren, ASCII-Steuerzeichen und Unicode-Zeilentrenner werden vor dem CSV-Schreiben zu Leerzeichen. Formelpräfixe `=`, `+`, `-` und `@` werden auch nach Unicode-Leerzeichen, BOM oder Zero-Width-Space mit einem Apostroph entschärft. Rohdaten werden nicht als HTML gerendert. Das ist eine wirksame Schutzmaßnahme gegen typische Spreadsheet-Formelinjektion, keine Garantie für jeden Tabellenimporter.

**EX4 – HTTP-Verträge:** CSV mit UTF-8-BOM, Semikolon, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; JSON enthält exakt den `/api/suche`-Antwortinhalt der gleichen Filterabfrage. `HEAD` liefert Header ohne Body.

**EX5 – negative Eingaben:** Ungültige Filter liefern HTTP 400 **ohne** Anhangs-Header. Bei null Treffern bleibt ein valider CSV-Header bzw. eine leere JSON-Trefferliste.

**EX6 – Browser:** Bereits integrierte CSV-/JSON-Links und ihr JavaScript-Abgleich mit dem aktiven Filterformular wurden durch eine lokale HTTP-/Asset-Prüfung kontrolliert. Ein echter Android-Browser-Ablauf ist damit nicht nachgewiesen.

**EX7 – Kosten/Quellen:** Tests nutzen den lokalen Server und synthetische eigene CSV-Angebote. Ausgeschlossene Fremdquellen werden beim Import entfernt. Der Export selbst führt keine Netzwerkanfrage zu externen Marktplätzen aus; GitHub-CI verwendete keine externen KI-Modelle.

**EX8 – Regressionen:** `tests/test_export_fertigstellung.py` enthält **neun** gezielte `unittest`-Testmethoden für JSON-Gleichheit, CSV-Spalten/Referenzpreis, Wiederimport einer harmlosen Eigenliste, Nulltreffer, Fehlerfilter, HEAD, Download-Links sowie Tabellenformel- und Fremdnetzschutz.

**Erfolgreicher Code-Testlauf:** Commit `abaca391ef031c43ad6224187bb8f5b30621ced8`, [GitHub Actions #40227202057](https://github.com/jefrey030/Schnapper/actions/runs/40227202057):
- Python **310 ausgeführte Tests, 1 übersprungen, 0 fehlgeschlagen**.
- Cloudflare **16/16 Tests bestanden, 0 übersprungen, 0 fehlgeschlagen**.
- Beide Jobs `success`. Ein abschließender Dokumentationscommit erfordert eine eigene CI-Kontrolle.

**EX9 – weiterhin offen:** Echte lizenzierte automatische Angebotsquellen, unabhängige Sicherheitsprüfung, tatsächlicher Android-Geräte-/Download-Test, Live-KI-Agenten, Hosting/Monitoring und Betreiberfreigabe für Merge/Deployment. Diese Aufgaben dürfen **nicht** als erledigt markiert werden. Das Hauptrepository `main` enthält ohne Merge weiterhin den historischen Stundenworkflow.

## Technische und betriebliche Schlussfolgerung

**Lokaler MVP:** Ergebnisexport fachlich vervollständigt und automatisiert getestet.  
**Automatische Live-Schnäppchen-App:** noch nicht fertig.  
**Vier autonome KI-Agenten:** nicht als produktiv laufend belegt.  
**Externe Dienste, Kosten, Veröffentlichungen, Merge:** keine Aktivierung.  
**Freigabestatus:** **NO-GO**.

