# SCHNAPPER MASTER 87 – Fertigstellung des aktiven lokalen Not-Aus

**Datum:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Sicherheitsbasis:** MASTER 86 / [PR #121](https://github.com/jefrey030/Schnapper/pull/121), HEAD `ec18ffea8873b47fa9152499ad2a31ec5b01d351`  
**Integrationsquelle:** eigenständiger [PR #92](https://github.com/jefrey030/Schnapper/pull/92) (aktive STOP-Prüfung); Quell-Branch nicht verändert.  
**Arbeitsbranch:** `integration/master87-active-stop-20261025`  
**Kosten:** 0 € extra, keine Modell-Downloads, keine Cloud-/Bezahl-API, keine produktive Bereitstellung.  
**Freigabe:** DRAFT. CODE-GO abhängig von finalem CI, MAIN-/PROD-/LIVE-GO weiterhin gesperrt.

## P0-Befund aus der realen Codeprüfung

Das vorherige `einmal()` startete jede KI-Rolle mittels `subprocess.run(..., timeout=240)`. Die Betreiberdatei `team/work/STOP` wurde nur **zwischen** den Rollen geprüft. Beim Setzen des Not-Aus während einer laufenden Rolle konnte der direkte Python-Agentenprozess daher noch bis zu vier Minuten weiterlaufen.

PR #92 enthielt bereits eine passende, separat entwickelte `Popen`-Hilfsfunktion. Um dessen ältere Gesamtdatei nicht blind zu übernehmen, wurden ausschließlich die relevante Funktion und die zwei notwendigen Aufruf-/Fehlerbehandlungsstellen **in die aktuelle MASTER86-Kette** integriert. Atomare KI-Aufrufquote, strenge Ollama-Abschlussprüfung, sieben Byte-gebundene Artefakte und sichere permanente Runner-Sperre bleiben erhalten.

## Tatsächliche Codeänderungen

- `team/local_service.py`: neuer `rolle_starten`-Prozessadapter auf fester Python-Befehlsliste ohne Shell. `Popen.communicate(timeout <= 0.5)` erlaubt regelmäßige STOP-Prüfung. Bei gesetztem STOP: `terminate()`, maximal zwei Sekunden warten, gegebenenfalls `kill()`; fehlgeschlagener Prozessbeleg mit Exit `-4` und ohne Teil-Logs. Bei allgemeinem Prozessstartfehler: `-5`; am Agentenlimit weiter kontrollierter Timeout.
- `BERICHT` darf nach Agentenausfall/STOP zur Dokumentation ausgeführt werden, führt aber **keine weitere KI-Rolle** aus.
- Alle bestehenden Offline-Unit-Tests, die `einmal()` bisher an `subprocess.run` mockten, wurden **gezielt** auf `rolle_starten` umgestellt, damit keine realen Agenten aus synthetischen Tests gestartet werden.
- `tests/test_master87_active_stop.py`: 17 weitere rein offline simulierte Regressionstests für STOP während des Aufrufs, Timeout, Prozessende, Startfehler, Folgerollen-Blockade, sichere Parameter und BERICHT-Ausnahme.
- Diese Datei: Abnahmeplan mit 66 Punkten.

## 66-Punkte-Fertigstellungs- und Abnahmematrix

| Nr. | Bereich | Prüfschritt |
|---:|---|---|
| 1 | A | PR121 MASTER86 HEAD verifizieren |
| 2 | A | PR92 aktive STOP-Reparatur unabhängig prüfen |
| 3 | A | PR92 nicht direkt in main mergen |
| 4 | A | Eigenen MASTER87-Zweig von getestetem HEAD erstellen |
| 5 | A | Master86 Ollama-Abschlussprüfung erhalten |
| 6 | A | Atomare lokale Quotenreservierung erhalten |
| 7 | A | Harte lokale Aufrufobergrenze erhalten |
| 8 | A | Lokalen Modell-/API-Endpunkt unverändert lassen |
| 9 | A | PR92 und fremde Branches unverändert lassen |
| 10 | A | 0 € Zusatzkosten und kein Deploy |
| 11 | B | Stop auch während laufendem Unterprozess prüfen |
| 12 | B | Popen mit fester Argumentliste statt Shell verwenden |
| 13 | B | Subprozess-Logs weiterhin abfangen |
| 14 | B | Regelmäßige Überwachung im halben Sekundenfenster |
| 15 | B | STOP vor Start verhindert neue Rolle |
| 16 | B | STOP während Rolle führt zu negativem Exit -4 |
| 17 | B | Kindprozess zuerst mit terminate stoppen |
| 18 | B | Nach 2-Sekunden-Wartefenster kill verwenden |
| 19 | B | Teil-Logs bei STOP nicht als Beleg übernehmen |
| 20 | B | Timeout 240 Sekunden weiterhin erzwingen |
| 21 | B | Timeout-Kindprozess killen und als Fehler markieren |
| 22 | B | Subprozess-Startfehler sicher mit -5 behandeln |
| 23 | B | BERICHT nach STOP als Protokollfunktion erlauben |
| 24 | B | Nach aktivem STOP keine weiteren kostenrelevanten Rollen |
| 25 | B | LEAD/BRAIN/CHECK/COMMAND Reihenfolge erhalten |
| 26 | C | Alte subprocess.run-Mocks auf neue Schnittstelle anpassen |
| 27 | C | MASTER77-Mocktest erhalten |
| 28 | C | MASTER78-Prozessnachweise erhalten |
| 29 | C | MASTER82-Prozessbindung erhalten |
| 30 | C | MASTER83-Artefaktbindung erhalten |
| 31 | C | MASTER85-Runnerlock-Test erhalten |
| 32 | C | Erfolgreichen simulierten Abschluss testen |
| 33 | C | Nichtnull-Exitcode unverändert erkennen |
| 34 | C | STOP vor Spawn blockiert |
| 35 | C | STOP während laufender Rolle terminiert |
| 36 | C | STOP bei Antwortende verhindert Teil-PASS |
| 37 | C | Bei hängendem Kind kill erzwingen |
| 38 | C | Unmittelbares Timeout testen |
| 39 | C | Timeout nach erster Überwachung simulieren |
| 40 | C | BERICHT nach STOP separat testen |
| 41 | C | BERICHT bleibt von STOP-Meldung verschont |
| 42 | C | Unsichere subprocess-Parameter zurückweisen |
| 43 | C | Fehlgeschlagenen Agentenstart protokollieren |
| 44 | C | STOP verhindert Folgerollen |
| 45 | C | Popen niemals mit shell=True aufrufen |
| 46 | C | BERICHT-Startfehler bewirkt keine positive Freigabe |
| 47 | D | Exakte Pull-Request-Basis und HEAD dokumentieren |
| 48 | D | MASTER87 Draft-PR erstellen |
| 49 | D | GitHub Python Volltest am finalen SHA ausführen |
| 50 | D | GitHub Cloudflare Offline-Volltest am finalen SHA ausführen |
| 51 | D | S-006 Ref-Gate nicht überspringen |
| 52 | D | Neue STOP-Tests im tatsächlichen CI-Log verifizieren |
| 53 | D | Testgesamtzahlen und Fehler nachweisen |
| 54 | D | Bei CI-Fail ausschließlich eigenen Zweig reparieren |
| 55 | D | Keine CI-Aktivierung bezahlter Runner |
| 56 | D | Keine Secrets oder personenbezogenen Daten loggen |
| 57 | E | Dokumentieren dass direkte Prozesse, nicht Ollama-Server, beendet werden |
| 58 | E | Kein Versprechen bereits erfolgte Requests rückgängig zu machen |
| 59 | E | Unterprozess-Kinder in eigenen Prozessgruppen weiter als Restrisiko behandeln |
| 60 | E | Unabhängigen Sicherheitsreview weiter verlangen |
| 61 | E | Android/Termux Endtest noch ausstehend kennzeichnen |
| 62 | E | Vier reale KI-Inferenzen nicht als bewiesen behaupten |
| 63 | E | Sicherheits-PRs noch nicht in main integriert |
| 64 | E | Keine Main-Änderung, kein Merge |
| 65 | E | Kein Deployment, keine Branchlöschung, keine bezahlte API |
| 66 | E | Keine Produktionsfreigabe trotz grüner Offline-Tests |

## Abnahme-Gates

**CODE-GO:** ausschließlich erfolgreicher GitHub-Actions-Python- und Cloudflare-Testlauf am finalen HEAD; S-006 explizit `ok` statt `skipped`; neue MASTER87-Tests müssen in den Logs als `ok` erscheinen.

**REVIEW-GO:** unabhängiger Security-Review und konfliktbewusste Integration aller bisherigen Drafts weiter erforderlich.

**LIVE-GO:** keine echten vier KI-Antworten unabhängig nachgewiesen; lokale Host-/Termux-/Android-Tests bleiben offen. Ein gestoppter lokaler Clientprozess garantiert *nicht*, dass ein bereits separat gestarteter Ollama-Server die Bearbeitung tatsächlich einstellt. Direktes Kindprozess-STOP ist außerdem keine Prozessgruppen-Terminierung.

**PROD-GO:** kein Auto-Merge, keine Bearbeitung von main, kein Deployment, keine Task-Autonomie, keine KI-API-Kosten und kein ungeprüfter Zugriff auf Echtangebote oder Kundendaten.

Die Prüfpunkte sind eine überprüfbare Aufgaben- und Evidenzmatrix, **keine pauschale Behauptung, dass jeder reale Betriebsschritt abgeschlossen sei**.
