# SCHNAPPER – Sicherheitsabnahme und Release-Sperren (22.10.2026)

**Entscheidung:** NICHT BESTANDEN / PRODUKTION GESPERRT. Dieses Dokument ersetzt weder echte Testlogs noch eine Betreiberfreigabe. Kostenbudget: **0 €**.

## Nachweisstand (Repository und read-only Cloudflare-Prüfung)

- Das GitHub-Repository ist privat. Tests und Stunden-Workflows werden per Workflow-If in privaten Repos kostenbewusst **übersprungen**; `skipped` ist ausdrücklich **kein PASS**.
- Für Cloudflare sind weder `schnapper-agent-team` noch die D1-Datenbank nachgewiesen. Billing-Read fehlt (403), Workers-Free-Tarif ist nicht nachgewiesen. **Keine Ressourcen aktivieren.**
- Lokale Python-/Node-Tests und D1-Simulationen müssen für die aktuelle Commit-SHA erneut ausgeführt und ihre Rohlogs gesichert werden. Alte Testerfolge beweisen keine Änderungen in diesem Branch.
- GitHub-`main` war am 22.10. ungeschützt (`protected=false`). Vor öffentlicher Freigabe Branchschutz und erforderliche Checks nachweisen.
- Open Prices und eBay sind als echte produktive Datenquellen nicht abgenommen.

## Abnahmekriterien je Agent (für TEST/STAGING)

| Agent | Pflichtnachweis |
| --- | --- |
| LEAD | Drei gültige Testaufgaben nacheinander anstoßen; eindeutige ID, nachvollziehbare Priorisierung, keine doppelte Abarbeitung |
| BRAIN | Zehn Testangebote mit validierter Quelle, Zeitpunkt und Preis; kein erfundener Preis, keine als echt ausgegebenen Mockdaten |
| CHECK | Manipulierten Preis, Duplikat, ungültige Quelle und leere Testliste erkennen; `abgelehnt`/`nachbessern` blockiert jede positive Gesamtbewertung |
| COMMAND | Drei gültige Übergaben protokollieren; `freigabe=nein` verhindert positive Gesamtbewertung; keine autonomen Deployments oder Käufe |

**Gemeinsame Sicherheitsprüfung:** Keine Geheimnisse in Ausgaben, kein bezahlter Provider, kein ungeprüfter Schreibzugriff, begrenzte Wiederholungen, nachvollziehbare Trace-/Aufgaben-IDs.

## Not-Aus / Monitoring

### Lokale Ausführung
Not-Aus-Datei: `team/work/STOP`. **Anlegen**, um neue KI-Prozesse und den nächsten Stundenlauf zu verhindern. Ein bereits laufender externer Modellaufruf kann erst nach seiner Rückkehr gestoppt werden. Nach Untersuchung muss die Datei **bewusst manuell** entfernt werden. Zusätzlich Prozess/Dienst beenden, falls sofortige Unterbrechung erforderlich ist.

### Cloudflare – ausschließlich nach Free-Nachweis und isoliertem Setup
Das D1-Schema legt `schnapper_control(id=1,paused=1)` an (default STOP). Ohne lesbare Zeile oder wenn `paused != 0` wird kein neuer KI-Aufruf gestartet. Vor jeder Rolle wird neu geprüft.

**Not-Aus mit D1-SQL:**
```sql
UPDATE schnapper_control
SET paused=1, reason='Betreiber-Not-Aus', updated_utc=datetime('now')
WHERE id=1;
```
**Aufhebung ausschließlich mit ausdrücklicher Freigabe**, nach Sicherheitsprüfungen:
```sql
UPDATE schnapper_control
SET paused=0, reason='Staging-Freigabe dokumentiert', updated_utc=datetime('now')
WHERE id=1;
```
Eine bereits gestartete Modellanfrage kann nicht rückwirkend abgebrochen werden. Cloudflare-`RUN_ENABLED=false` und Entfernen von Cron dienen als weitere Abschaltebenen.

Monitoring **noch nicht produktiv implementiert**: unabhängigen Heartbeat, Alarme bei fehlenden Berichten, Quoten-/Fehlerüberwachung und Not-Aus-Probe vor Abnahme nachweisen. Niemals ein fehlendes Heartbeat als Erfolg deuten.

## Strikte Umgebungsgrenzen

**TEST:** Python-Unittests und Node-`node --test cloudflare/test/worker.test.mjs` ohne Live-Provider ausführen. Gezielt negative Fälle prüfen (Not-Aus, DB-Ausfall, Fehler bei Secret-Scan, ungültige Rollenrückmeldung, Bezahl-Anbieter blockiert). SHA und Rohlogs speichern. TEST darf keine Produktionszugänge verwenden.

**STAGING:** Eigene Worker-Instanz, eigene D1-Datenbank, eigenständige Bindings, Daten und Schlüssel. Initial `RUN_ENABLED=false`, `paused=1` und **kein Cron**. Erst nach **belegtem** Workers-Free-Tarif manuell aktivieren. 24 Stunden Monitoring, 3 vollständige Teamzyklen, 2 unmittelbar aufeinanderfolgende echte Stundenläufe und erfolgreiche Not-Aus-Probe nachweisen. Echte Open-Prices-Abfragen nur GET/lesend, begrenzt und mit Quellnachweis. Keine Kauf-/Schreibaktionen.

**PRODUKTION:** Separater Worker, D1-Datenbank, Berechtigungen, Konfiguration und Logs; nie Staging-Daten recyceln. Standard `RUN_ENABLED=false`, `paused=1`, kein Cron. Produktivzugriff erst nach bestandenem Staging, unabhängiger Sicherheitsprüfung, bestätigtem 0-€-Tarif, aktivem Monitoring, Rollback, GitHub-Branchschutz und **ausdrücklicher erneuter Betreiberfreigabe**.

## Harte Freigabebedingung

Nur `PASS`, wenn alle Prüfungen für alle vier Agenten echte, aktuelle Belege besitzen; die gesamte Produktionsumgebung kontrolliert ist; ein Not-Aus-Praxistest erfolgreich war; Kosten sicher auf 0 € begrenzt sind; GitHub-Checks `success` statt `skipped` melden; und der Betreiber ausdrücklich bestätigt.

Bei `FAIL`, `SKIPPED`, unbekanntem Tarif, fehlendem Monitoring oder unklarem Zugriff bleibt der Betrieb **BLOCKIERT**. Dokumentation, Simulation, Code-Präsenz und bloße KI-Behauptungen zählen nie als erfolgreiche Live-Abnahme.

## Nachtrag – Sicherheitsprüfung auf PR #21 (22.10.2026)

**Nicht bestanden / kein Release.** Zusätzliche Sicherungen sind im Entwicklungsbranch
gespeichert, aber die vollständige Test-Suite wurde für diesen neuen Commit noch nicht
ausgeführt. In privaten Repositories sind die GitHub Actions bewusst `skipped`.

- Der finale Stundenbericht prüft jetzt zusätzlich LEAD-, BRAIN-, CHECK- und
  COMMAND-Antworten auf bekannte Geheimnismuster. Nur Rollennamen (nie den Schlüssel)
  werden bei einem Fund im Prüffeld `ki_geheimnis_rollen` protokolliert.
- Bereits vor dem Schreiben eines Agenten-Rohberichts werden gefundene Schlüssel
  zu `[REDACTED]` maskiert. Ein solcher Fund setzt den gespeicherten Agentenstatus
  auf `FEHLER` und führt zu einem nicht erfolgreichen Prozess-Exit.
- BRAIN-Vorschläge werden ebenfalls vor persistenter Ablage maskiert. Ungefilterte
  KI-Rohantworten erscheinen nicht mehr als Vorschau in der Konsole.
- Die neuen Regressionstests prüfen für LEAD, CHECK und COMMAND den fehlenden
  positiven Teamstatus **und** die Redigierung in den tatsächlich geschriebenen
  JSON-Dateien.
- Das Muster ist eine Defense-in-Depth-Erkennung bekannter Tokenformate, kein
  vollständiger DLP-Ersatz. Vor einem öffentlichen Repo müssen Logs, bestehende
  Historie/Artefakte und Secrets zusätzlich gescannt und bereinigt werden.

**Abnahme noch ausstehend:** Python- und Node-Tests für diese SHA, echter
Not-Aus-Test, unabhängiges Review, Free-Tarif-Nachweis und zwei echte
aufeinanderfolgende Teamläufe. Weder GitHub- noch Cloudflare-Produktivjobs starten.
