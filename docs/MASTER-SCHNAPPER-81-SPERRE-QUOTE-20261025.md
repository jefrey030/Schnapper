# SCHNAPPER MASTER 81 – Begrenzte Dateisperre und sichere lokale KI-Quote

**Datum:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Ausgangsbasis:** MASTER 80, [Draft-PR #102](https://github.com/jefrey030/Schnapper/pull/102), HEAD `41c793319067245bd684bfad29268368d5823ad1`  
**Eigener Branch:** `fix/master81-counter-quota-lock-timeout-20261025`  
**Priorität:** P0 Betriebssperren und Aufrufquote; P1 Offline-Regression  
**Budget:** 0 € Zusatzkosten. Nur kostenfreie öffentliche CI-Standardrunner und synthetische Daten.  
**Freigabe:** DRAFT / NO-GO für Merge, Deployment, produktiven Vier-KI-Dienst und reale Daten.

## Gesicherter Befund

MASTER 80 verwendet die Dateisperre `fcntl.flock(LOCK_EX)` ohne Begrenzung der Wartezeit. Ein konkurrierender oder hängender Prozess kann dadurch einen Agentenstart unbegrenzt blockieren. Zugleich las der historische gemeinsame KI-Konfigurationsbaustein `SCHNAPPER_MAX_AUFRUFE` direkt mit `int()` aus der Umgebung, ohne eine harte Obergrenze: fehlerhafte Eingaben konnten einen Importfehler verursachen; große positive Zahlen konnten die lokale sechs-Aufrufe-Grenze aufheben.

## Tatsächliche Änderungen

- `team/local_ollama.py`: `_hole_zaehlersperre()` wartet mit `LOCK_EX | LOCK_NB` und begrenzten kurzen Versuchen auf die lokale Datei. Nach maximal zwei Sekunden wird die Anfrage klar abgelehnt. Nicht-kontentionsbedingte Betriebssystemfehler werden nicht verdeckt.
- `team/local_ollama.py`: ein Aufruflimit außerhalb ganzzahliger Werte 1–6 wird sowohl bei Konstruktion als auch vor der Reservierung abgelehnt. Keine lokale Modell-/Netzwerkabfrage bei ungültigem Limit.
- `team/ki.py`: `_sicheres_aufruflimit()` akzeptiert ausschließlich Zeichenketten `1` bis `6`. Sonst liefert es `0`, das im lokalen Adapter aktiv blockiert; kein Python-Importabsturz durch `int('ungültig')`.
- `tests/test_master81_lock_quota.py`: 17 zusätzliche reine Offline-Testmethoden, darunter Lock-Kollisionen, Timeout, unbekannte Betriebssystemfehler, veränderte Quoten und nicht angerührte persistente Zähler.

## 30-Punkte-Master / Abnahme

| # | Arbeitspaket | Abnahmebedingung |
| -: | --- | --- |
| 01 | Projekt verifizieren | jefrey030/Schnapper |
| 02 | MASTER-80-Ausgangs-HEAD prüfen | 41c793319067245bd684bfad29268368d5823ad1 |
| 03 | Bestehende PRs nicht ändern | #55/#69/#80/#89/#94/#97/#101/#102 getrennt |
| 04 | Eigener Branch | gestapelt auf MASTER 80 |
| 05 | Root-Cause dokumentieren | MAX_AUFRUFE aus Env und flock ohne Timeout |
| 06 | Keine externen API-Aufrufe | nur Offline-Testsimulation |
| 07 | Feste Quotengrenze | maximal 6 lokale Reservierungen |
| 08 | Sicherer Konfigurationsparser | ungültig => 0/sperren |
| 09 | Kein Import-Absturz bei Fehleingabe | sicherer Parser statt ungeschütztes int |
| 10 | Deaktivierte Konfiguration | 0 blockiert |
| 11 | Überhöhte Konfiguration | 7+, große Zahlen blockieren |
| 12 | Formatfehler | -1/3.0/Leerzeichen/03 blockiert |
| 13 | Bool-Wert | nicht als 1 akzeptieren |
| 14 | Modell vor Kostenprüfung verhindern | bereits beim KI-Init blockieren |
| 15 | Quota unmittelbar beim Zählen prüfen | kein nachträglicher Bypass |
| 16 | LOCK_EX | LOCK_NB | nur nichtblockierende Versuche |
| 17 | Kurz begrenztes Warten | maximal zwei Sekunden |
| 18 | EAGAIN erneut probieren | kurze Retry-Pause |
| 19 | EACCES erneut probieren | gleiches Zeitlimit |
| 20 | Unbekannte OS-Fehler | ohne Freigabe weitergeben |
| 21 | Sperre nicht verfügbar | KI-Lauf fail-closed |
| 22 | Zähler bei Fehler unangetastet lassen | bestehenden Wert erhalten |
| 23 | Sechs saubere Reservierungen | MASTER-80-Regressionsfälle bleiben |
| 24 | Parallelzugriff | bestehender ThreadPool-Test bleibt grün |
| 25 | 17 zusätzliche Testmethoden | tests/test_master81_lock_quota.py |
| 26 | Python-Gesamttests | kein sicherheitsrelevanter Ausfall |
| 27 | Cloudflare Offline-Tests | keine Bereitstellung |
| 28 | Finalen HEAD und CI-Joblogs prüfen | Commit-SHA stimmt |
| 29 | Unabhängigen Review verlangen | keine automatische Freigabe |
| 30 | Kosten- und Produktionsgrenzen | 0 €; kein Deploy/Merge |

## Sicherheitsgrenzen

- Keine Live-Ollama- oder Cloud-KI-Aufrufe; keine Modelle installieren oder herunterladen.
- Keine Änderungen an `main`, den bisherigen Sicherheits-PRs oder fremden Arbeitszweigen.
- Keine automatischen Merges, Freigaben, Käufe, Kostenaktivierungen oder Deployments.
- Der Nachweis belegt ausschließlich die synthetisch geprüfte Zähler- und Sperrlogik, **keine real ausgeführte Vier-KI-Rotation**.
- Weiterhin bestehende Risiken: Manipulation durch lokal privilegierte Akteure, Locking-Unterschiede auf nicht unterstützten Plattformen, Dateisystem-Crash-Szenarien, unabhängige Modellattestierung fehlt.
- Das direkte Lesen des `SCHNAPPER_MAX_AUFRUFE`-Werts erfolgt zur Modulinitialisierung; spätere Umgebungsänderungen erfordern einen neuen Prozess.

**CI- und Freigaberegel:** Python- und Cloudflare-Offline-Tests auf dem *finalen* Commit prüfen. Erst nach unabhängiger Sicherheitsprüfung darf eine menschliche Merge-Entscheidung vorbereitet werden. Bis dahin: **NO-GO**.
