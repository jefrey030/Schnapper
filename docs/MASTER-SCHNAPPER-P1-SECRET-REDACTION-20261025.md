# SCHNAPPER – Master P1: Secret-Redaction und Fail-Closed-Protokolle
**Datum:** 25.10.2026 | **Branch:** `integration/schnapper-p0-mainbased-20261025` | **Bestehender Draft:** [#55](https://github.com/jefrey030/Schnapper/pull/55)  
**Budget:** 0 € zusätzliche Kosten | **Release-Status:** NO-GO | **Modus:** Nur isolierte GitHub-Änderungen + Offline-CI

## Hauptauftrag
Die nachgewiesene Fehlerprotokoll-Schwachstelle des Cloudflare-Workers absichern und verhindern, dass von einem Modell oder einem Provider versehentlich ausgegebene Zugangsdaten in D1, Logs oder Statusantworten landen. Bestehende Sicherheitsregeln und Kostenkontrolle bleiben erhalten. Keine fremden Daten lesen und keine Live-Modelle ausführen.

## Gelesener Ist-Zustand
1. `main` auf Commit `6dbe114271b332ed9d4c282b50c4ce02b112ac49` führt weiterhin einen Legacy-Stundenworkflow aus; neuester gelesener Zeitlauf [40195297304](https://github.com/jefrey030/Schnapper/actions/runs/40195297304) vom 25.10.2026. Grüne Workflow-Anzeige allein ist **kein KI-Nachweis**.
2. Draft [#55](https://github.com/jefrey030/Schnapper/pull/55), Integrationsbasis `main`, hat bisher Python 236 Tests (1 SKIP), Cloudflare 13/13 bestanden am SHA `1343665fe050c51d525f72b6487748a3d640ff73`, Run [40155527454](https://github.com/jefrey030/Schnapper/actions/runs/40155527454).
3. Der Cloudflare Worker `cloudflare/src/worker.mjs` speichert Modell-Antworttexte direkt in `schnapper_reports`. Die Catch-Behandlung kopiert `error.message` bisher ungefiltert in den D1-Status, die Konsole und den zurückgegebenen Status. Wenn darin ein Token steht, gelangt der Token in gespeicherte oder externe Protokolle.
4. `team/agent.py` hat bereits geheime Tokenmuster für lokale Agentenausgaben; der Cloudflare-Worker benötigt äquivalente Negativregressionen, ohne echte Zugangsdaten zu benutzen.

## Ausführungsaufträge, voneinander getrennt
| Rolle | Konkreter Auftrag | Gate |
| --- | --- | --- |
| LEAD | Quellen-/PR-Stand prüfen, Dopplungen vermeiden, P0-Blocker `main`-Cron offen halten | Keine Behauptung über vier aktive externe KIs |
| BRAIN | Geschützte Fehlerbehandlung einbauen, Modellantworten auf typische Tokenindikatoren prüfen und bei Fund abbrechen | Kein fremder Token gelangt in D1/Logs |
| CHECK | Negative Worker-Mocktests für Modelltext und Providerfehler ergänzen; GitHub-CI an derselben Commit-SHA prüfen | Python/Cloudflare beide PASS, SKIP korrekt ausgewiesen |
| COMMAND | Run-/SHA-Nachweis, Sperrstatus, Restblocker und Kostenkontrolle dokumentieren | Kein Merge, keine Produktion, keine kostenpflichtige Nutzung |

## Regeln für die Umsetzung
- Nur vorhandenen Draft #55 ergänzen; **nicht** `main` verändern, Deployment starten, Runner konfigurieren oder einen weiteren redundanten PR eröffnen.
- Alle Secret-Testwerte ausschließlich synthetisch und ohne gültige Tokens; keine Geheimnisse anzeigen, versenden oder archivieren.
- Bei einem verdächtigen KI-Text: kein Speichern des Textes und kein als erfolgreich markierter Gesamtbericht; statt dessen ein generischer Blockiergrund.
- Bei einem geheimnishaltigen API-/D1-Fehler: **Redaction vor** Protokoll, D1-Markierung und Rückgabe.
- Statische Tests sind keine realen Modellantworten. Vier KI-Rollen auf GitHub-Issues sind Arbeitsrollen, keine selbstständig gestarteten KI-Instanzen.

## Abnahmeprotokoll (wird nach Ausführung ergänzt)
- [x] Echtes Commit mit Secret-Redaction und Ablehnung verdächtiger Modellantworten
- [x] Regression: synthetischer Token in Modellantwort nicht in Report gespeichert
- [x] Regression: synthetischer Token in Fehler nicht im zurückgegebenen Status, D1-Markierung oder Konsolen-Log
- [x] GitHub CI `python-tests`: 238 Tests, 1 SKIP, 0 FAIL – [Run 40197764731](https://github.com/jefrey030/Schnapper/actions/runs/40197764731)
- [x] GitHub CI `cloudflare-tests`: 16/16 Tests PASS – [Run 40197764731](https://github.com/jefrey030/Schnapper/actions/runs/40197764731)
- [x] Geprüfte Code-SHA `1c6a61bce27bb9f04a9913098f9d0f21a53f40cb` und CI #40197764731 dokumentiert; Dokumentationscommit selbst wird zusätzlich nachgeprüft
- [x] Unabhängige Produktions-/Security-Abnahme ausdrücklich offen (**NO-GO**)

## Release-Sperren
#55 bleibt Review-Draft. `main`-Cron und Backend-Stilllegung sind erst nach überprüftem und ausdrücklich freigegebenem Merge behoben. Cloudflare- und Ollama-Betrieb sind ohne echte Host-/Kontrollnachweise nicht freigegeben. `GitHub Actions: success` ersetzt keine Sicherheitsprüfung der Produktion.

## Erledigter zweiter Sicherheitsblock

**Zusätzlicher Befund:** `team/local_service.py` kontrollierte bisher nur das Vorhandensein einer Agentendatei, nicht ihre inhaltliche Übereinstimmung mit dem aggregierten Bericht. So konnte sogar eine Mock-Testdatei mit bloßem Rollennamen einen positiven lokalen Pilot-Gate passieren, wenn der Sammelbericht andere positive Fakten behauptete. Dies ist ein Nachweis-Konsistenzproblem, keine behauptete Fernzugriffslücke.

**Implementiert:** Für jede der vier Rollen wird der konkrete JSON-Inhalt der Datei gelesen und mit dem jeweiligen Agentenobjekt im Sammelbericht verglichen. Fehlende, ungültige und widersprüchliche Dateien blockieren den positiven Pilot-Nachweis. Der frühere positive Test wurde auf tatsächlich konsistente Mock-Dateien umgestellt; zwei negative Tests prüfen Unterschiede und unlesbares JSON.

**Nachweise:** [PR #55](https://github.com/jefrey030/Schnapper/pull/55), überprüfte Commit-SHA `1c6a61bce27bb9f04a9913098f9d0f21a53f40cb`, [GitHub Actions #40197764731](https://github.com/jefrey030/Schnapper/actions/runs/40197764731):
- `python-tests`: 238 Tests, OK, 1 übersprungen, 0 Fehler.
- `cloudflare-tests`: 16 Tests, 16 bestanden, 0 Fehler.
- Die fünf neuen Regressionen sind reine lokale Simulationen mit künstlichen Zeichenfolgen; keine realen Tokens oder Cloud-Modelle wurden benötigt.

**Grenzen / offene Entscheidung:** Übereinstimmende Dateien allein belegen keine kryptografisch authentifizierten Modellantworten. Der Public-Repository-`main`-Stundenjob ist weiterhin nicht abgeschaltet, weil der Draft nicht gemergt wurde. Realer Ollama-Betrieb, Staging, Produktionsbetrieb, Testtarif und vollständige unabhängige Sicherheitsprüfung sind nicht nachgewiesen. Release-Status bleibt **NO-GO**. 0 € Zusatzkosten.
